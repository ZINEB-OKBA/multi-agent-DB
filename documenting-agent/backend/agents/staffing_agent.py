"""
agents/staffing_agent.py
────────────────────────────────────────────────────────────────────
Agent principal Staffing.

Pipeline :
  1. Reçoit les fichiers du projet (PDF/Excel) déjà décodés depuis PostgreSQL
  2. Extrait les données via OCR ou Pandas (staffing_extractor)
  3. Calcule TJM, coûts, rentabilité (staffing_calculator)
  4. Génère les graphiques (staffing_charts)
  5. Passe la synthèse + question au LLM pour une réponse narrative
  6. Retourne { answer, charts, sources }

Intégration dans orchestrator.py :
  elif intent == "staffing":
      from agents.staffing_agent import run_staffing_agent
      result = run_staffing_agent(question, project_id, docs_raw)
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from utils.staffing_extractor  import extract_from_dataframe, extract_from_pdf_bytes
from utils.staffing_calculator import compute_staffing_analysis
from utils.staffing_charts     import generate_staffing_charts
from utils.llm_factory          import get_llm
from langchain_core.prompts         import ChatPromptTemplate
from langchain_core.output_parsers  import StrOutputParser

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# PROMPT LLM STAFFING
# ══════════════════════════════════════════════════════════════════

STAFFING_PROMPT = ChatPromptTemplate.from_template(
    """Tu es un analyste RH et financier expert en gestion du staffing.
Tu travailles avec les données réelles d'un projet d'entreprise.

══════════════════════════════════════════════
DONNÉES DE STAFFING CALCULÉES :
══════════════════════════════════════════════
{synthese}

══════════════════════════════════════════════
RÈGLES DE RÉPONSE :
══════════════════════════════════════════════
1. Réponds UNIQUEMENT à partir des données ci-dessus.
2. Réponds directement et précisément à la question posée par l'utilisateur. Ne donne pas d'informations superflues ou d'autres chiffres si la question ne le demande pas.
3. Si la question est générale (ex: synthèse globale), affiche le tableau de synthèse et explique brièvement les points clés.
4. Si l'utilisateur pose une question sur un employé spécifique, concentre ta réponse exclusivement sur cet employé et ne parle pas des autres.
5. Ne donne des recommandations, d'analyses de rentabilité/gain/perte ou de taux d'occupation que si la question le demande ou y fait référence.
6. Utilise des tableaux Markdown et mets en **gras** les chiffres importants pour plus de lisibilité.
7. NE génère JAMAIS de liens d'images Markdown (ex: `![Nom](url_image.png)`) ou de balises HTML d'images (`<img>`). Les graphiques sont gérés et injectés automatiquement par l'application, tu ne dois pas essayer de les dessiner en format texte ou markdown.
8. Sois direct. Ne fais pas de longues introductions, réponds immédiatement à la question.
9. NE fais JAMAIS de mentions ou d'hypothèses sur les couleurs des graphiques (ex: ne dis pas qu'un élément est rouge, vert, etc.) car le style visuel est géré dynamiquement par l'interface.
10. Si la question demande d'identifier ou de désigner un collaborateur spécifique (ex: le plus rentable, le moins occupé, etc.), réponds directement en nommant ce collaborateur et en donnant ses chiffres clés. Ne liste pas tous les autres collaborateurs du projet sous forme de tableau ou de liste si ce n'est pas explicitement demandé.
11. Évite absolument les répétitions et ne génère jamais de tableaux vides ou tronqués à la fin de ta réponse. Tu ne dois générer qu'une seule et unique section ou un seul tableau de données dans toute ta réponse. Il est strictement interdit d'afficher le même tableau, les mêmes données ou les mêmes lignes de collaborateurs plusieurs fois (par exemple, ne fais jamais une section "Données", puis une section "Analyse", puis une section "Graphique" avec les mêmes chiffres).
12. NE MENTIONNE JAMAIS l'absence de fichiers Excel ou le fait que les données proviennent d'un fichier PDF ou RAG. Si tu as les données de staffing calculées ci-dessus, présente-les simplement comme les données du projet, sans mentionner des messages d'erreur passés ou des limites de format source.
13. N'essaie jamais de dessiner, simuler ou représenter le graphique demandé sous forme de tableau texte ou markdown. Contente-toi de faire l'analyse en texte. L'application se charge déjà d'afficher le graphique visuel à part. Ta réponse ne doit contenir aucun placeholder ou introduction de graphique comme "Graphique :" ou "Voici le graphique :" suivis d'un tableau répété.
14. Si plusieurs collaborateurs portent le même prénom ou nom de base dans les données (ex: "Zakaria (ID: 8)" et "Zakaria (ID: 11)") et que l'utilisateur pose une question générale ou sur ce nom, tu ne dois JAMAIS les regrouper ou sommer leurs chiffres. Tu dois impérativement les traiter comme deux personnes distinctes et afficher toujours leur ID complet (ex: "Zakaria (ID: 8)" et "Zakaria (ID: 11)") pour éviter toute confusion.
15. Lorsque tu compares des valeurs numériques (par exemple pour déterminer quel projet ou employé a un gain net, coût, budget ou salaire plus élevé), fais extrêmement attention à l'ordre de grandeur des chiffres. Par exemple, 13 142 Dhs est supérieur à 3 714 Dhs. Vérifie toujours tes affirmations comparatives avant de répondre.

{history_section}

QUESTION DE L'UTILISATEUR :
{question}

Réponds en français, de manière structurée et professionnelle.
RÉPONSE :"""
)


# ══════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ══════════════════════════════════════════════════════════════════

def run_staffing_agent(
    question:    str,
    docs_raw:    List[Dict[str, Any]],   # liste de {file_name, content_bytes, suffix}
    force_employe: Optional[str] = None,
    history: Optional[List[dict]] = None,
    theme_mode: Optional[str] = "light",
) -> Dict[str, Any]:
    """
    Paramètres
    ----------
    question     : question posée par l'utilisateur
    docs_raw     : fichiers du projet [{file_name, file_bytes, suffix}]
    force_employe: filtrer sur un employé spécifique (extrait de la question si None)

    Retourne
    --------
    {
      "answer":  "texte narratif HTML-ready",
      "charts":  [ {title, type, base64, chartjs} ],
      "sources": [ {fileName, pages, extractCount} ],
      "error":   None ou message d'erreur
    }
    """
    result = {"answer": "", "charts": [], "sources": [], "error": None}

    # ── 1. Extraire les données de tous les fichiers ──────────────
    all_records: List[Dict[str, Any]] = []
    sources_used: List[Dict[str, Any]] = []

    for doc in docs_raw:
        file_name  = doc.get("file_name", "fichier")
        file_bytes = doc.get("file_bytes", b"")
        suffix     = doc.get("suffix", "").lower()

        try:
            if suffix in (".xlsx", ".xls", ".xlsm", ".csv"):
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                if suffix == ".csv":
                    df = pd.read_csv(tmp_path)
                else:
                    df = pd.read_excel(tmp_path)
                os.unlink(tmp_path)

                records = extract_from_dataframe(df)

            elif suffix in (".pdf", ".doc", ".docx"):
                records = extract_from_pdf_bytes(file_bytes, file_name)

            else:
                logger.warning(f"Format non supporté par l'agent staffing : {suffix}")
                continue

            if records:
                all_records.extend(records)
                sources_used.append({
                    "fileName":     file_name,
                    "pages":        None,
                    "extractCount": len(records),
                })
                logger.info(f"✅ {len(records)} records extraits de '{file_name}'")

        except Exception as e:
            logger.error(f"Erreur extraction '{file_name}': {e}")

    if not all_records:
        result["error"] = (
            "⚠️ Aucune donnée de staffing n'a pu être extraite des fichiers du projet. "
            "Vérifiez que les fichiers contiennent des colonnes : Employé, Mois, Jours, TJM."
        )
        result["answer"] = result["error"]
        return result

    logger.info(f"📊 Total records staffing : {len(all_records)}")

    # Si l'utilisateur demande explicitement tous les collaborateurs, un bilan global ou complet, on n'hérite pas du filtre de l'historique
    lower_q = question.lower()
    is_global_request = any(kw in lower_q for kw in ["tous", "tout", "toute", "toutes", "chaque", "global", "général", "general", "complet", "liste"])

    # ── 2. Détecter l'année dans la question et filtrer les records ──
    year_filter = _extract_year_from_question(question)
    if not year_filter and history and not is_global_request:
        for h in reversed(history[-6:]):
            if h.get("role") == "user":
                year_filter = _extract_year_from_question(h.get("content", ""))
                if year_filter:
                    logger.info(f"📅 Année {year_filter} récupérée depuis l'historique récent.")
                    break

    if year_filter:
        filtered_records = [r for r in all_records if r.get("mois", "").startswith(year_filter)]
        if filtered_records:
            all_records = filtered_records
            logger.info(f"📅 Filtrage par année {year_filter} : {len(all_records)} records conservés.")
        else:
            all_records = []
            logger.warning(f"⚠️ Aucun record trouvé pour l'année {year_filter}.")

    # ── 3. Détecter l'employé dans la question ────────────────────
    employes_found = _extract_employes_from_question(question, all_records) if all_records else []
    
    # Si l'utilisateur demande explicitement tous les collaborateurs, un bilan global ou complet, on n'hérite pas du filtre de l'historique
    lower_q = question.lower()
    is_global_request = any(kw in lower_q for kw in ["tous", "tout", "toute", "toutes", "chaque", "global", "général", "general", "complet", "liste"])

    if not employes_found and not force_employe and history and not is_global_request:
        for h in reversed(history[-6:]):
            if h.get("role") == "user":
                employes_found = _extract_employes_from_question(h.get("content", ""), all_records)
                if employes_found:
                    logger.info(f"👤 Employés {employes_found} récupérés depuis l'historique récent.")
                    break

    # Déterminer la valeur finale pour employe_filter (chaîne unique, liste ou None)
    if force_employe:
        employe_filter = force_employe
    elif len(employes_found) > 1:
        employe_filter = employes_found
    elif len(employes_found) == 1:
        employe_filter = employes_found[0]
    else:
        employe_filter = None

    # ── 4. Détecter le projet dans la question ────────────────────
    projet_filter = _extract_projet_from_question(question, all_records) if all_records else None
    if not projet_filter and history and not is_global_request:
        for h in reversed(history[-6:]):
            if h.get("role") == "user":
                projet_filter = _extract_projet_from_question(h.get("content", ""), all_records)
                if projet_filter:
                    logger.info(f"📁 Projet {projet_filter} récupéré depuis l'historique récent.")
                    break

    # ── 5. Extraire les paramètres financiers de la question ──────
    ca_facturable           = _extract_amount(question, ["ca", "chiffre d'affaires", "facturé", "ca facturable"])
    cout_journalier_interne = _extract_amount(question, ["coût interne", "salaire journalier", "cout journalier"])

    # ── 6. Calculer l'analyse ─────────────────────────────────────
    if not all_records and year_filter:
        analysis = {"erreur": f"Aucune donnée de staffing disponible pour l'année {year_filter}."}
    else:
        analysis = compute_staffing_analysis(
            records                  = all_records,
            employe_filter           = employe_filter,
            projet_filter            = projet_filter,
            ca_facturable            = ca_facturable,
            cout_journalier_interne  = cout_journalier_interne,
        )

    if analysis.get("erreur"):
        result["error"]  = analysis["erreur"]
        result["answer"] = analysis["erreur"]
        return result

    # ── 5. Générer les graphiques uniquement si demandés ──────────
    lower_q = question.lower()
    graph_keywords = ["graphe", "graphique", "chart", "plot", "barre", "courbe", "diagramme", "barchart", "piechart", "dessine", "représente", "visuelle", "visualiser", "char", "pie", "bar", "grap", "line"]
    if any(kw in lower_q for kw in graph_keywords):
        # 1. Détection du nombre (limite du classement)
        top_n = None
        match_n = re.search(r"\b(?:top|les|classement)\s*(\d+)\b", lower_q)
        if match_n:
            top_n = int(match_n.group(1))
            
        # 2. Détection de la métrique
        metric = None
        if any(kw in lower_q for kw in ["coût", "cout", "cher", "depense", "dépense"]):
            metric = "cost"
        elif any(kw in lower_q for kw in ["occupé", "occupe", "travail", "jours", "activité", "activite"]):
            metric = "days"
        elif any(kw in lower_q for kw in ["rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable"]):
            metric = "gain"
            
        # 3. Détection de l'ordre
        order = None
        if any(kw in lower_q for kw in ["moins", "pire", "minimum", "min", "bas"]):
            order = "asc"
        elif any(kw in lower_q for kw in ["top", "plus", "meilleur", "maximum", "max"]):
            order = "desc"
            
        # 4. Détection du type de graphique
        chart_type = None
        if any(kw in lower_q for kw in ["pie", "camembert", "tarte"]):
            chart_type = "pie"
        elif any(kw in lower_q for kw in ["bar", "barre", "histogramme"]):
            chart_type = "bar"

        # 5. Héritage des paramètres de classement manquants depuis l'historique
        if history and (top_n is None or metric is None or order is None or chart_type is None):
            for h in reversed(history[-6:]):
                if h.get("role") == "user":
                    hist_content = h.get("content", "").lower()
                    if top_n is None:
                        m = re.search(r"\b(?:top|les|classement)\s*(\d+)\b", hist_content)
                        if m:
                            top_n = int(m.group(1))
                    if metric is None:
                        if any(kw in hist_content for kw in ["coût", "cout", "cher", "depense", "dépense"]):
                            metric = "cost"
                        elif any(kw in hist_content for kw in ["occupé", "occupe", "travail", "jours", "activité", "activite"]):
                            metric = "days"
                        elif any(kw in hist_content for kw in ["rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable"]):
                            metric = "gain"
                    if order is None:
                        if any(kw in hist_content for kw in ["moins", "pire", "minimum", "min", "bas"]):
                            order = "asc"
                        elif any(kw in hist_content for kw in ["top", "plus", "meilleur", "maximum", "max"]):
                            order = "desc"
                    if chart_type is None:
                        if any(kw in hist_content for kw in ["pie", "camembert", "tarte"]):
                            chart_type = "pie"
                        elif any(kw in hist_content for kw in ["bar", "barre", "histogramme"]):
                            chart_type = "bar"

        # Valeurs par défaut finales
        if top_n is None: top_n = 5
        if metric is None: metric = "gain"
        if order is None: order = "desc"
        if chart_type is None: chart_type = "bar"
            
        charts = generate_staffing_charts(
            analysis, 
            employe_filter, 
            theme_mode=theme_mode, 
            top_n=top_n, 
            metric=metric, 
            order=order, 
            chart_type=chart_type
        )
        
        # 6. Détection du sujet (topic_q) pour le filtrage thématique
        topic_q = lower_q
        topic_keywords = [
            "rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable", "top", "meilleur", "moins", "plus", "classement",
            "projet", "projets", "tjm", "salaire", "salaires", "saliare", "saliares", "salarie", "salaries", "paye", "paie", "gagne", "gagné",
            "rémunération", "remuneration", "occupation", "jours", "jour", "travail", "charge", "temps", "occupe", "occupé", "activité", "activite",
            "coût", "cout", "dépense", "depense", "évolution", "evolution", "mensuel"
        ]
        if not any(kw in lower_q for kw in topic_keywords) and history:
            for h in reversed(history[-6:]):
                if h.get("role") == "user":
                    hist_content = h.get("content", "").lower()
                    if any(kw in hist_content for kw in topic_keywords):
                        topic_q = hist_content
                        logger.info(f"📋 Sujet hérité de l'historique : {topic_q}")
                        break

        # Filtrage thématique précis sur topic_q
        matched_charts = []
        
        # 1. Rentabilité / Top employés / Classements
        if any(kw in topic_q for kw in ["rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable", "top", "meilleur", "moins", "plus", "classement"]):
            if any(emp_kw in topic_q for emp_kw in ["employe", "employé", "employer", "collaborateur", "ressource", "chaque", "tous", "comparatif"]) or employe_filter:
                matched_charts.extend([c for c in charts if c.get("title") in ["Classement des employés rentables", "Classement des employés par coût", "Classement des employés par activité"]])
                matched_charts.extend([c for c in charts if c.get("title") == "Taux de gain par employé"])
            else:
                matched_charts.extend([c for c in charts if c.get("title") == "Rentabilité"])
            
        # 2. Répartition par projet
        if "projet" in topic_q or (any(kw in topic_q for kw in ["repartition", "répartition", "camembert", "pie"]) and not any(kw in topic_q for kw in ["employe", "employé", "employer", "collaborateur"])):
            matched_charts.extend([c for c in charts if c.get("title") == "Répartition par projet"])
            
        # 3. Salaire mensuel comparatif / TJM
        if any(kw in topic_q for kw in ["tjm", "salaire", "salaires", "saliare", "saliares", "salarie", "salaries", "paye", "paie", "gagne", "gagné", "comparatif", "rémunération", "remuneration", "tjm comparatif"]):
            matched_charts.extend([c for c in charts if "salaire" in c.get("title", "").lower() or "tjm" in c.get("title", "").lower() or "comparatif des employés" in c.get("title", "").lower()])
            
        # 4. Occupation mensuelle
        if any(kw in topic_q for kw in ["occupation", "jours", "jour", "travail", "charge", "temps", "occupe", "occupé", "activité", "activite"]):
            matched_charts.extend([c for c in charts if c.get("title") == "Occupation mensuelle"])
            
        # 5. Coût mensuel (historique/évolution, non lié aux projets ou à la rentabilité)
        if any(kw in topic_q for kw in ["coût", "cout", "dépense", "depense", "évolution", "evolution", "mensuel"]) and not any(kw in topic_q for kw in ["projet", "rentabilité", "rentabilite"]):
            matched_charts.extend([c for c in charts if c.get("title") == "Coût mensuel"])

        # Si des filtres thématiques ont correspondu, on filtre la liste
        if matched_charts:
            # Supprimer les doublons tout en gardant l'ordre
            seen = set()
            charts = [c for c in matched_charts if c.get("title") not in seen and not seen.add(c.get("title"))]
            
            # Si l'utilisateur a spécifié un type de graphique particulier (ex: pie, bar, line), on filtre également par ce type
            if "pie" in lower_q or "camembert" in lower_q:
                charts = [c for c in charts if c.get("type") == "pie"]
            elif "bar" in lower_q or "barre" in lower_q:
                charts = [c for c in charts if c.get("type") == "bar"]
            elif "line" in lower_q or "courbe" in lower_q:
                charts = [c for c in charts if c.get("type") == "line"]
        else:
            # Si aucun filtre thématique n'a fonctionné, on ne renvoie pas tout par défaut,
            # SAUF si l'utilisateur a explicitement demandé de voir tous les graphiques / tableaux de bord
            if any(kw in lower_q for kw in ["tous les", "toutes les", "chaque", "dashboard", "tableau de bord", "tous ses", "tous les graphiques", "tous les graphes", "affiche les graphes", "les graphiques", "les graphes", "les diagrammes"]):
                if "pie" in lower_q or "camembert" in lower_q:
                    charts = [c for c in charts if c.get("type") == "pie"]
                elif "line" in lower_q or "courbe" in lower_q:
                    charts = [c for c in charts if c.get("type") == "line"]
                elif "bar" in lower_q or "barre" in lower_q:
                    charts = [c for c in charts if c.get("type") == "bar"]
            else:
                charts = []
    else:
        charts = []
    result["charts"] = charts
    logger.info(f"📈 {len(charts)} graphiques générés après filtrage.")

    # ── 6. Appeler le LLM avec la synthèse ────────────────────────
    synthese = analysis.get("synthese", "")
    history_section = ""
    if history:
        history_section = "\n══════════════════════════════════════════════\nHISTORIQUE DES ÉCHANGES RÉCENTS :\n══════════════════════════════════════════════\n"
        for h in history[-8:]:
            role = "Utilisateur" if h.get("role") == "user" else "Assistant"
            content = h.get("content", "")
            if len(content) > 500:
                content = content[:500] + "..."
            history_section += f"- {role} : {content}\n"

    try:
        llm   = get_llm(temperature=0.1, max_tokens=2048)
        chain = STAFFING_PROMPT | llm | StrOutputParser()
        answer = chain.invoke({"synthese": synthese, "question": question, "history_section": history_section})
    except Exception as e:
        logger.error(f"Erreur LLM staffing : {e}")
        answer = synthese   # fallback : retourner la synthèse calculée directement

    result["answer"]  = answer
    result["sources"] = sources_used
    return result


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _extract_year_from_question(question: str) -> Optional[str]:
    """Extrait une année à 4 chiffres (ex: 2024, 2026) de la question."""
    match = re.search(r"\b(20\d{2})\b", question)
    if match:
        return match.group(1)
    return None


def _extract_employes_from_question(question: str, records: List[Dict]) -> List[str]:
    """
    Cherche tous les noms d'employés connus mentionnés dans la question.
    Retourne la liste des noms exacts.
    """
    employes = list({r["employe"] for r in records if r.get("employe")})
    q_lower  = question.lower()
    matched = []

    for emp in employes:
        # Correspondance exacte (avec ID)
        if emp.lower() in q_lower:
            matched.append(emp)
            continue
        # Essayer sans parenthèses pour l'ID
        emp_clean_id = emp.lower().replace("(", "").replace(")", "").replace(":", "")
        if emp_clean_id in q_lower:
            matched.append(emp)
            continue
        # Essayer avec le nom de base
        base_name = re.sub(r"\s*\(id:\s*\d+\)", "", emp, flags=re.IGNORECASE).strip().lower()
        parts = base_name.split()
        if any(p in q_lower for p in parts if len(p) > 2):
            matched.append(emp)

    seen = set()
    return [x for x in matched if not (x in seen or seen.add(x))]


def _extract_employe_from_question(question: str, records: List[Dict]) -> Optional[str]:
    """
    Cherche si un nom d'employé connu est mentionné dans la question.
    Retourne le nom exact (ou le nom de base si plusieurs possèdent ce nom) ou None.
    """
    matched = _extract_employes_from_question(question, records)
    return matched[0] if matched else None


def _extract_amount(question: str, keywords: List[str]) -> Optional[float]:
    """Extrait un montant numérique précédé d'un mot-clé dans la question."""
    q_lower = question.lower()
    for kw in keywords:
        if kw in q_lower:
            # Cherche un nombre après le mot-clé
            pattern = re.compile(
                rf"{re.escape(kw)}\s*[:=]?\s*(\d[\d\s.,]*)", re.IGNORECASE
            )
            m = pattern.search(q_lower)
            if m:
                try:
                    return float(m.group(1).replace(" ", "").replace(",", "."))
                except ValueError:
                    pass
    return None


def _extract_projet_from_question(question: str, records: List[Dict]) -> Optional[str]:
    """
    Cherche si un nom de projet connu est mentionné dans la question.
    Retourne le nom exact ou None.
    """
    projets = list({r["projet"] for r in records if r.get("projet")})
    q_lower = question.lower()
    for proj in projets:
        if proj.lower() in q_lower:
            logger.info(f"Projet détecté dans la question : {proj}")
            return proj
    return None