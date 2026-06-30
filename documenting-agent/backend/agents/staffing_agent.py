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

from utils.staffing_extractor  import extract_from_dataframe, extract_from_multiple_dataframes, extract_from_pdf_bytes
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
16. Si l'utilisateur demande un graphique ou un pourcentage de répartition, ne fais aucun calcul de pourcentage toi-même dans le texte. Indique simplement que le graphique en forme de tarte (pie chart) généré ci-dessous montre la répartition.
17. ATTENTION ORTHOGRAPHE : L'utilisateur peut écrire "employer" au lieu de "employé". Dans le contexte de l'application, "employer" ou "employeur" désigne TOUJOURS un "employé" (le collaborateur, la ressource) et non pas un projet ou un client. Ne fais jamais de regroupement par projet/client si l'utilisateur demande "par employer".
18. CJM ET INFOS CIBLÉES : CJM signifie "Coût Journalier Moyen" (et non pas "Temps de Travail Moyen"). Si l'utilisateur demande une métrique précise (ex: uniquement le CJM, uniquement le salaire, ou uniquement les jours travaillés), n'affiche jamais le tableau global de synthèse avec toutes les autres colonnes. Génère à la place un tableau restreint avec uniquement le nom de l'employé et la métrique spécifiquement demandée (ex: "Employé" et "Coût Journalier Moyen (CJM)").
19. CALCUL DE LA RENTABILITÉ / MARGE : La formule financière standard de la marge de rentabilité est toujours : Marge = Gain Net / Chiffre d'Affaires (CA). Ne divise JAMAIS le Gain Net par le Coût pour calculer la marge ou la rentabilité. Si le gain net est de 35 285,72 Dhs et le CA généré est de 60 000,00 Dhs, la rentabilité est de 58.8% (35 285.72 / 60 000.00), et non pas 146%.
20. DEVISE ET MONNAIE : Toutes les valeurs financières (salaires, coûts, budgets, gains, etc.) doivent obligatoirement être exprimées en Dirhams (écrire "Dh" ou "Dhs"). Il est strictement interdit d'utiliser le symbole de l'Euro (€) ou du Dollar ($).
21. RETOUR SUR INVESTISSEMENT (ROI) GLOBAL : Le ROI global d'un projet se calcule TOUJOURS par la formule : ROI = Gain Net Global / Coût Total. Pour le projet Motul, le budget/CA total est de 20 000,00 Dhs et le coût total est de 20 952,38 Dhs, soit un Gain Net de -952,38 Dhs et un ROI de -4.5%. Pour le projet CT, le budget/CA total est de 60 000,00 Dhs et le coût total est de 24 714,28 Dhs, soit un Gain Net de +35 285,72 Dhs et un ROI de 142.8%. Ne confonds pas le ROI global (divisé par le Coût) avec la Marge de rentabilité (divisée par le CA). Présente toujours ces calculs globaux et exacts au niveau du projet si l'utilisateur demande le ROI ou le gain global du projet.
22. INTERDICTION DE FAIRE DES CALCULS MANUELS : Il est strictement interdit d'effectuer des calculs mathématiques (comme des additions, soustractions, divisions pour trouver le ROI, le gain net total ou le taux de marge) par toi-même. Utilise UNIQUEMENT et STRICTEMENT les valeurs pré-calculées fournies dans la section "DONNÉES DE STAFFING CALCULÉES" (notamment les colonnes Gain net, Marge de rentabilité, et Retour sur investissement (ROI) du tableau "Synthèse par Projet"). Ne fais aucun arrondi ou recalcul manuel.
23. QUESTIONS SIMPLES / DE COMPTAGE / LISTES : Si l'utilisateur pose une question de comptage simple (ex: "combien d'employés...", "combien de projets...") ou une question de liste simple (ex: "liste des collaborateurs", "quels employés ont démarré en 2018 ?", "l'employé qui a démarré à telle date..."), tu dois répondre directement et uniquement par une phrase concise ou une liste à puces claire avec l'information demandée (ex: "Il existe 25 employés dans les données."). Il est STRICTEMENT INTERDIT d'afficher de grands tableaux financiers (contenant des colonnes de coûts calculés, CJM, CA, gain net, etc.) ou la synthèse par projet lorsque la question ne le demande pas.
24. INTERDICTION D'UTILISER LE TERME "TJM" : Il est strictement interdit d'utiliser le terme "TJM" (Taux Journalier Moyen) ou d'en faire référence dans tes réponses pour parler des collaborateurs. Utilise uniquement et exclusivement le terme "CJM" (Coût Journalier Moyen) pour désigner le coût ou tarif journalier d'un employé.
25. PRIORITÉ AUX NOUVELLES DONNÉES SUR L'HISTORIQUE : Si la section HISTORIQUE DES ÉCHANGES RÉCENTS ci-dessous contient des réponses ou des chiffres qui diffèrent des "DONNÉES DE STAFFING CALCULÉES" fournies ci-dessus (par exemple en raison d'un changement de fichier Excel ou de base de données), tu dois IMPÉRATIVEMENT ignorer les chiffres de l'historique et utiliser uniquement les chiffres de la section "DONNÉES DE STAFFING CALCULÉES". Les données de la section "DONNÉES DE STAFFING CALCULÉES" écrasent toute ancienne conversation.
26. MOIS ABSENTS DANS LE DÉTAIL : Si un mois spécifique demandé par l'utilisateur (ex: janvier) n'apparaît pas dans la table "Détail mensuel" de l'employé, cela signifie obligatoirement que l'employé a travaillé 0 jour (aucune imputation) ce mois-là. Réponds avec "0 jour" pour ce mois absent.
27. EXPLICATION DU DÉTAIL DES CALCULS : Si l'utilisateur demande comment un chiffre a été obtenu ou s'il demande le "détail du calcul" (notamment pour le coût total, le gain net, le ROI ou la marge d'un projet ou d'un collaborateur), tu dois obligatoirement détailler chaque étape du calcul par une formule simple et claire (ex: "Gain Net = CA du projet (903 200,00 Dhs) - Coût total cumulé de tous les collaborateurs (109 685,66 Dhs) = 793 514,34 Dhs"). Affiche toujours ces calculs intermédiaires.
28. DISTINCTION COLLABORATEUR VS PROJET GLOBAL : Si la question porte sur un collaborateur spécifique (ex: Anass Naji) et sa rentabilité sur un projet, fais extrêmement attention à ne pas mélanger son coût individuel (ex: 23 785,65 Dhs) avec le coût total cumulé de tous les collaborateurs sur ce projet (ex: 109 685,66 Dhs). Explique clairement que le gain net et le ROI globaux du projet sont calculés sur la base du coût total de tous les collaborateurs travaillant sur le projet, et non sur le seul coût de ce collaborateur individuel. Affiche toujours le coût total cumulé du projet à côté pour que l'utilisateur comprenne la logique de calcul.


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

    dfs_to_extract = []
    excel_csv_files = []

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
                    dfs_to_extract.append(df)
                else:
                    sheet_dict = pd.read_excel(tmp_path, sheet_name=None)
                    for sheet_name, df in sheet_dict.items():
                        logger.info(f"Fiche Excel '{file_name}' - feuille '{sheet_name}' chargée (shape: {df.shape})")
                        dfs_to_extract.append(df)
                os.unlink(tmp_path)
                excel_csv_files.append(file_name)

            elif suffix in (".pdf", ".doc", ".docx"):
                records = extract_from_pdf_bytes(file_bytes, file_name)
                if records:
                    all_records.extend(records)
                    sources_used.append({
                        "fileName":     file_name,
                        "pages":        None,
                        "extractCount": len(records),
                    })
                    logger.info(f"✅ {len(records)} records extraits de '{file_name}'")

            else:
                logger.warning(f"Format non supporté par l'agent staffing : {suffix}")
                continue

        except Exception as e:
            logger.error(f"Erreur extraction '{file_name}': {e}")

    if dfs_to_extract:
        try:
            excel_records = extract_from_multiple_dataframes(dfs_to_extract)
            if excel_records:
                all_records.extend(excel_records)
                for fn in excel_csv_files:
                    sources_used.append({
                        "fileName":     fn,
                        "pages":        None,
                        "extractCount": len(excel_records),
                    })
                logger.info(f"✅ {len(excel_records)} records extraits au total des fichiers Excel/CSV")
        except Exception as e:
            logger.error(f"Erreur lors de la fusion/extraction des DataFrames Excel/CSV : {e}")

    if not all_records:
        result["error"] = (
            "⚠️ Aucune donnée de staffing n'a pu être extraite des fichiers du projet. "
            "Vérifiez que les fichiers contiennent des colonnes : Employé, Mois, Jours, CJM."
        )
        result["answer"] = result["error"]
        return result

    logger.info(f"📊 Total records staffing : {len(all_records)}")

    # Si l'utilisateur demande explicitement tous les collaborateurs, un bilan global ou complet, on n'hérite pas du filtre de l'historique
    lower_q = question.lower()
    is_global_request = any(kw in lower_q for kw in ["tous", "tout", "toute", "toutes", "chaque", "global", "général", "general", "complet", "liste", "par employé", "par employe", "par employer", "par collaborateur", "par projet", "par mois", "comparatif", "classement", "répartition", "repartition"])
    is_hiring_query = any(kw in lower_q for kw in ["debuter", "débuter", "demarrer", "démarrer", "recrute", "embauche", "démarrage", "demarrage", "date de debut", "date de demarrage", "commencer", "commence"])

    # ── 2. Détecter l'année ou une date précise dans la question ──
    year_filter = _extract_year_from_question(question)
    date_match = re.search(r"\b(20\d{2}[-/]\d{2}[-/]\d{2})\b", question)
    date_filter = date_match.group(1).replace("/", "-") if date_match else None

    if not year_filter and not date_filter and history and not is_global_request:
        for h in reversed(history[-6:]):
            if h.get("role") == "user":
                hist_q = h.get("content", "")
                year_filter = _extract_year_from_question(hist_q)
                dm = re.search(r"\b(20\d{2}[-/]\d{2}[-/]\d{2})\b", hist_q)
                date_filter = dm.group(1).replace("/", "-") if dm else None
                if year_filter or date_filter:
                    logger.info("📅 Année/Date récupérée depuis l'historique récent.")
                    break

    if date_filter and is_hiring_query:
        filtered_records = [r for r in all_records if r.get("date_demarrage", "").startswith(date_filter)]
        if filtered_records:
            all_records = filtered_records
            logger.info(f"📅 Filtrage par date de démarrage exacte {date_filter} : {len(all_records)} records conservés.")
        else:
            all_records = []
            logger.warning(f"⚠️ Aucun record trouvé avec la date de démarrage {date_filter}.")
    elif year_filter:
        if is_hiring_query:
            filtered_records = [r for r in all_records if r.get("date_demarrage", "").startswith(year_filter)]
        else:
            filtered_records = [r for r in all_records if r.get("mois", "").startswith(year_filter)]

        if filtered_records:
            all_records = filtered_records
            logger.info(f"📅 Filtrage par année {year_filter} : {len(all_records)} records conservés.")
        else:
            # Si on ne trouve rien avec le filtre d'année mois, on essaie comme fallback sur la date de démarrage
            fb_records = [r for r in all_records if r.get("date_demarrage", "").startswith(year_filter)]
            if fb_records:
                all_records = fb_records
                logger.info(f"📅 Fallback filtrage par année de démarrage {year_filter} : {len(all_records)} records.")
            else:
                all_records = []
                logger.warning(f"⚠️ Aucun record trouvé pour l'année {year_filter}.")

    # ── 3. Détecter l'employé dans la question ────────────────────
    employes_found = _extract_employes_from_question(question, all_records) if all_records else []
    
    # Si l'utilisateur demande explicitement tous les collaborateurs, un bilan global ou complet, on n'hérite pas du filtre de l'historique
    lower_q = question.lower()
    is_global_request = any(kw in lower_q for kw in ["tous", "tout", "toute", "toutes", "chaque", "global", "général", "general", "complet", "liste", "par employé", "par employe", "par employer", "par collaborateur", "par projet", "par mois", "comparatif", "classement", "répartition", "repartition"])

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
    is_project_list_request = any(kw in lower_q for kw in ["projets", "les projet", "les projets", "quel projet", "quels projets", "sur quoi", "travaillé sur", "travaille sur"])
    if not projet_filter and history and not is_global_request and not is_project_list_request:
        for h in reversed(history[-6:]):
            if h.get("role") == "user":
                proj_candidate = _extract_projet_from_question(h.get("content", ""), all_records)
                if proj_candidate:
                    # Vérifier si l'employé filtré travaille sur ce projet candidat
                    if employe_filter:
                        emp_list = [employe_filter] if isinstance(employe_filter, str) else employe_filter
                        has_records = False
                        for emp_f in emp_list:
                            has_records = any(
                                emp_f.lower() in str(r.get("employe", "")).lower() and
                                proj_candidate.lower() in str(r.get("projet", "")).lower()
                                for r in all_records
                            )
                            if has_records:
                                break
                        if not has_records:
                            logger.info(f"📁 Projet candidat {proj_candidate} ignoré car l'employé {employe_filter} n'y travaille pas.")
                            continue
                    
                    projet_filter = proj_candidate
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
            question                 = question,
        )

    if analysis.get("erreur"):
        result["error"]  = analysis["erreur"]
        result["answer"] = analysis["erreur"]
        return result

    # ── 5. Générer les graphiques uniquement si demandés ──────────
    lower_q = question.lower()
    graph_keywords = ["graphe", "graphique", "chart", "plot", "barre", "courbe", "diagramme", "barchart", "piechart", "dessine", "représente", "visuelle", "visualiser", "char", "pie", "bar", "grap", "line", "camembert", "tarte", "radar", "toile", "araignée", "araignee"]
    if any(kw in lower_q for kw in graph_keywords):
        # 1. Détection du nombre (limite du classement)
        top_n = None
        
        # Convertir les mots de nombres français en chiffres
        french_numbers = {
            "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
            "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10
        }
        
        q_for_num = lower_q
        for word, val in french_numbers.items():
            q_for_num = re.sub(rf"\b{word}\b", str(val), q_for_num)
            
        match_n = re.search(r"\b(?:top|les|classement|pour|de|seulement|uniquement)\s*(\d+)\b", q_for_num)
        if not match_n:
            match_n = re.search(r"\b(\d+)\s*(?:employe|employé|collaborateur|pers|salarie)", q_for_num)
        if not match_n:
            # Fallback simple sur n'importe quel chiffre seul entre 1 et 25
            for m in re.finditer(r"\b(\d+)\b", q_for_num):
                val = int(m.group(1))
                if 1 <= val <= 25:
                    top_n = val
                    break
        else:
            top_n = int(match_n.group(1))
            
        # 2. Détection de la métrique
        metric = None
        if any(kw in lower_q for kw in ["coût", "cout", "cher", "depense", "dépense"]):
            metric = "cost"
        elif any(kw in lower_q for kw in ["occupé", "occupe", "travail", "jours", "activité", "activite"]):
            metric = "days"
        elif any(kw in lower_q for kw in ["rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable"]):
            metric = "gain"
        elif any(kw in lower_q for kw in ["salaire", "salaires", "saliare", "saliares", "salarie", "salaries", "paye", "paie", "rémunération", "remuneration"]):
            metric = "salary"
        elif any(kw in lower_q for kw in ["tjm", "cjm"]):
            metric = "cjm"
            
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
        elif any(re.search(rf"\b{kw}\b" if kw == "bar" else kw, lower_q) for kw in ["bar", "barre", "histogramme"]):
            chart_type = "bar"
        elif any(kw in lower_q for kw in ["radar", "toile", "araignée", "araignee"]):
            chart_type = "radar"

        # 5. Héritage des paramètres de classement manquants depuis l'historique
        if history and (top_n is None or metric is None or order is None or chart_type is None):
            for h in reversed(history[-6:]):
                if h.get("role") == "user":
                    hist_content = h.get("content", "").lower()
                    
                    # Convertir les nombres français dans l'historique aussi
                    h_q_for_num = hist_content
                    for word, val in french_numbers.items():
                        h_q_for_num = re.sub(rf"\b{word}\b", str(val), h_q_for_num)
                        
                    if top_n is None:
                        m = re.search(r"\b(?:top|les|classement|pour|de|seulement|uniquement)\s*(\d+)\b", h_q_for_num)
                        if not m:
                            m = re.search(r"\b(\d+)\s*(?:employe|employé|collaborateur|pers|salarie)", h_q_for_num)
                        if m:
                            top_n = int(m.group(1))
                    if metric is None:
                        if any(kw in hist_content for kw in ["coût", "cout", "cher", "depense", "dépense"]):
                            metric = "cost"
                        elif any(kw in hist_content for kw in ["occupé", "occupe", "travail", "jours", "activité", "activite"]):
                            metric = "days"
                        elif any(kw in hist_content for kw in ["rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable"]):
                            metric = "gain"
                        elif any(kw in hist_content for kw in ["salaire", "salaires", "saliare", "saliares", "salarie", "salaries", "paye", "paie", "rémunération", "remuneration"]):
                            metric = "salary"
                        elif any(kw in hist_content for kw in ["tjm", "cjm"]):
                            metric = "cjm"
                    if order is None:
                        if any(kw in hist_content for kw in ["moins", "pire", "minimum", "min", "bas"]):
                            order = "asc"
                        elif any(kw in hist_content for kw in ["top", "plus", "meilleur", "maximum", "max"]):
                            order = "desc"
                    if chart_type is None:
                        if any(kw in hist_content for kw in ["pie", "camembert", "tarte"]):
                            chart_type = "pie"
                        elif any(re.search(rf"\b{kw}\b" if kw == "bar" else kw, hist_content) for kw in ["bar", "barre", "histogramme"]):
                            chart_type = "bar"
                        elif any(kw in hist_content for kw in ["radar", "toile", "araignée", "araignee"]):
                            chart_type = "radar"

        # Valeurs par défaut finales
        if top_n is None:
            if any(kw in lower_q for kw in ["top", "classement"]):
                top_n = 5
            else:
                top_n = 20
        if metric is None: metric = "gain"
        if order is None: order = "desc"
        if chart_type is None: chart_type = "bar"
        logger.info(f"DEBUG RADAR: lower_q='{lower_q}'")
        logger.info(f"DEBUG RADAR: chart_type detected as '{chart_type}'")

        # Si des employés spécifiques sont mentionnés dans la question, on filtre par_employe pour les graphiques
        mentioned_employees = []
        par_emp = analysis.get("par_employe", {})
        q_for_names = lower_q.replace("charibi", "chraibi")
        for emp_key in par_emp.keys():
            clean_key = re.sub(r"\s*\(id:\s*\d+\)", "", emp_key).lower().strip()
            if clean_key in q_for_names:
                mentioned_employees.append(emp_key)
            else:
                parts = clean_key.split()
                if len(parts) >= 2 and all(part in q_for_names for part in parts if len(part) > 2):
                    mentioned_employees.append(emp_key)
                
        if mentioned_employees:
            analysis_for_charts = analysis.copy()
            analysis_for_charts["par_employe"] = {k: v for k, v in par_emp.items() if k in mentioned_employees}
        else:
            analysis_for_charts = analysis
            
        charts = generate_staffing_charts(
            analysis_for_charts, 
            employe_filter, 
            theme_mode=theme_mode, 
            top_n=top_n, 
            metric=metric, 
            order=order, 
            chart_type=chart_type
        )
        logger.info(f"DEBUG RADAR: generate_staffing_charts returned {len(charts)} charts")
        for c in charts:
            logger.info(f"  - Chart: '{c.get('title')}', type='{c.get('type')}'")
        
        # 6. Détection du sujet (topic_q) pour le filtrage thématique
        topic_q = lower_q
        topic_keywords = [
            "rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable", "top", "meilleur", "moins", "plus", "classement",
            "projet", "projets", "tjm", "cjm", "salaire", "salaires", "saliare", "saliares", "salarie", "salaries", "paye", "paie", "gagne", "gagné",
            "rémunération", "remuneration", "occupation", "jours", "jour", "travail", "charge", "temps", "occupe", "occupé", "activité", "activite",
            "coût", "cout", "dépense", "depense", "évolution", "evolution", "mensuel", "radar", "toile", "araignée", "araignee"
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
        
        # Détection des sujets spécifiques
        is_salary = any(kw in topic_q for kw in ["salaire", "salaires", "saliare", "saliares", "salarie", "salaries", "paye", "paie", "rémunération", "remuneration"])
        is_cjm = any(kw in topic_q for kw in ["tjm", "cjm", "tjm comparatif", "cjm comparatif"])
        is_days = any(kw in topic_q for kw in ["occupation", "jours", "jour", "travail", "charge", "temps", "occupe", "occupé", "activité", "activite"])
        is_cost = any(kw in topic_q for kw in ["coût", "cout", "dépense", "depense"]) and not any(kw in topic_q for kw in ["projet", "rentabilité", "rentabilite"])
        is_project = "projet" in topic_q or (any(kw in topic_q for kw in ["repartition", "répartition", "camembert", "pie"]) and not any(kw in topic_q for kw in ["employe", "employé", "employer", "collaborateur"]))
        is_radar = any(kw in topic_q for kw in ["radar", "toile", "araignée", "araignee"])

        if is_radar:
            if "projet" in topic_q:
                matched_charts.extend([c for c in charts if c.get("title") == "Répartition par projet"])
            elif any(x in topic_q for x in ["cjm", "tjm"]):
                matched_charts.extend([c for c in charts if c.get("title") == "CJM comparatif"])
            elif any(x in topic_q for x in ["salaire", "salaires"]):
                matched_charts.extend([c for c in charts if c.get("title") == "Salaire mensuel comparatif"])
            elif any(x in topic_q for x in ["gain", "perte", "rentable", "rentabilité"]):
                matched_charts.extend([c for c in charts if c.get("title") == "Classement des employés rentables"])
            else:
                matched_charts.extend([c for c in charts if c.get("title") == "Profil radar employés"])
        elif is_salary:
            matched_charts.extend([c for c in charts if "salaire" in c.get("title", "").lower()])
        elif is_cjm:
            matched_charts.extend([c for c in charts if any(x in c.get("title", "").lower() for x in ["tjm", "cjm"])])
        elif is_days:
            if any(emp_kw in topic_q for emp_kw in ["employe", "employé", "employer", "collaborateur", "ressource", "chaque", "tous", "comparatif"]) or employe_filter:
                matched_charts.extend([c for c in charts if c.get("title") == "Classement des employés par activité"])
            else:
                matched_charts.extend([c for c in charts if c.get("title") == "Occupation mensuelle"])
        elif is_cost:
            matched_charts.extend([c for c in charts if c.get("title") == "Coût mensuel" or c.get("title") == "Classement des employés par coût"])
        elif is_project:
            matched_charts.extend([c for c in charts if c.get("title") == "Répartition par projet"])

        # Si ce n'est aucun sujet de métrique spécifique, on applique la rentabilité / classement général
        if not matched_charts:
            if any(kw in topic_q for kw in ["rentabilité", "rentabilite", "gain", "perte", "bénéfice", "benefice", "rentable", "top", "meilleur", "moins", "plus", "classement"]):
                if any(emp_kw in topic_q for emp_kw in ["employe", "employé", "employer", "collaborateur", "ressource", "chaque", "tous", "comparatif"]) or employe_filter:
                    matched_charts.extend([c for c in charts if c.get("title") in ["Classement des employés rentables", "Classement des employés par coût", "Classement des employés par activité"]])
                    matched_charts.extend([c for c in charts if c.get("title") == "Taux de gain par employé"])
                else:
                    matched_charts.extend([c for c in charts if c.get("title") == "Rentabilité"])

        # Si des filtres thématiques ont correspondu, on filtre la liste
        if matched_charts:
            # Supprimer les doublons tout en gardant l'ordre
            seen = set()
            charts = [c for c in matched_charts if c.get("title") not in seen and not seen.add(c.get("title"))]
            
            # Si l'utilisateur a spécifié un type de graphique particulier (ex: pie, bar, line, radar), on filtre également par ce type
            if "pie" in lower_q or "camembert" in lower_q:
                charts = [c for c in charts if c.get("type") == "pie"]
            elif "barre" in lower_q or re.search(r"\bbar\b", lower_q):
                charts = [c for c in charts if c.get("type") == "bar"]
            elif "line" in lower_q or "courbe" in lower_q:
                charts = [c for c in charts if c.get("type") == "line"]
            elif "radar" in lower_q or "araignée" in lower_q:
                charts = [c for c in charts if c.get("type") == "radar"]
        else:
            # Si aucun filtre thématique n'a fonctionné, on ne renvoie pas tout par défaut,
            # SAUF si l'utilisateur a explicitement demandé de voir tous les graphiques / tableaux de bord
            if any(kw in lower_q for kw in ["tous les", "toutes les", "chaque", "dashboard", "tableau de bord", "tous ses", "tous les graphiques", "tous les graphes", "affiche les graphes", "les graphiques", "les graphes", "les diagrammes"]):
                if "pie" in lower_q or "camembert" in lower_q:
                    charts = [c for c in charts if c.get("type") == "pie"]
                elif "line" in lower_q or "courbe" in lower_q:
                    charts = [c for c in charts if c.get("type") == "line"]
                elif "barre" in lower_q or re.search(r"\bbar\b", lower_q):
                    charts = [c for c in charts if c.get("type") == "bar"]
                elif "radar" in lower_q or "araignée" in lower_q:
                    charts = [c for c in charts if c.get("type") == "radar"]
            # Log inside if block
            logger.info(f"DEBUG RADAR: matched_charts count={len(matched_charts)}")
            for c in matched_charts:
                logger.info(f"  - Matched Chart: '{c.get('title')}', type='{c.get('type')}'")
            logger.info(f"DEBUG RADAR: final charts count={len(charts)}")
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
        logger.warning(f"⚠️ Primary LLM failed: {e}. Attempting fallback model gemma2-9b-it...")
        try:
            from langchain_groq import ChatGroq
            fallback_llm = ChatGroq(
                model="gemma2-9b-it",
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.1,
                max_tokens=2048
            )
            chain = STAFFING_PROMPT | fallback_llm | StrOutputParser()
            answer = chain.invoke({"synthese": synthese, "question": question, "history_section": history_section})
            logger.info("✅ Fallback model gemma2-9b-it succeeded.")
        except Exception as fb_err:
            logger.warning(f"⚠️ Fallback gemma2-9b-it failed: {fb_err}. Attempting fallback llama-3.1-8b-instant...")
            try:
                from langchain_groq import ChatGroq
                fallback_llm2 = ChatGroq(
                    model="llama-3.1-8b-instant",
                    api_key=os.getenv("GROQ_API_KEY"),
                    temperature=0.1,
                    max_tokens=2048
                )
                chain = STAFFING_PROMPT | fallback_llm2 | StrOutputParser()
                answer = chain.invoke({"synthese": synthese, "question": question, "history_section": history_section})
                logger.info("✅ Fallback model llama-3.1-8b-instant succeeded.")
            except Exception as fb_err2:
                logger.error(f"❌ All fallback models failed. Final error: {fb_err2}")
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
    q_lower  = question.lower().replace("charibi", "chraibi")
    
    emp_scores = {}
    for emp in employes:
        emp_lower = emp.lower()
        # 1. Correspondance exacte complète (avec ID ou nom de base complet)
        base_name = re.sub(r"\s*\(id:\s*\d+\)", "", emp, flags=re.IGNORECASE).strip().lower()
        if base_name in q_lower or emp_lower in q_lower:
            emp_scores[emp] = 10
            continue
            
        # 2. Correspondance par parties (prénom / nom)
        parts = base_name.split()
        score = 0
        for p in parts:
            if len(p) >= 4 and p in q_lower:
                score += 1
        if score > 0:
            emp_scores[emp] = score

    if not emp_scores:
        return []

    # Ne garder que le ou les employés ayant le score maximal
    max_score = max(emp_scores.values())
    matched = [emp for emp, score in emp_scores.items() if score == max_score]

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
    Cherche si un nom de projet connu (ou une partie significative) est mentionné dans la question.
    Retourne le nom exact du projet ou None.
    """
    projets = list({r["projet"] for r in records if r.get("projet")})
    q_lower = question.lower()
    
    # 1. Essayer d'abord une correspondance exacte du nom de base entier
    for proj in projets:
        # Enlever l'année à la fin si présente (ex: " (2025)")
        base_proj = re.sub(r"\s*\(\d{4}\)\s*$", "", proj).strip().lower()
        if base_proj in q_lower:
            logger.info(f"Projet détecté via correspondance exacte du nom de base : {proj}")
            return proj
            
    # 2. Chercher les acronymes ou noms de clients spécifiques entre crochets/parenthèses
    best_match = None
    best_score = 0
    
    for proj in projets:
        bracket_match = re.search(r"\[(.*?)\]", proj)
        if bracket_match:
            client_part = bracket_match.group(1).lower()
            if client_part in q_lower:
                score = len(client_part)
                if score > best_score:
                    best_score = score
                    best_match = proj
            
            paren_match = re.search(r"\((.*?)\)", client_part)
            if paren_match:
                acronym = paren_match.group(1).strip().lower()
                if re.search(rf"\b{re.escape(acronym)}\b", q_lower):
                    score = 10
                    if score > best_score:
                        best_score = score
                        best_match = proj
                        
            words = re.findall(r"\b\w{3,}\b", client_part)
            for w in words:
                if w not in ("bank", "group", "assurance") and re.search(rf"\b{re.escape(w)}\b", q_lower):
                    score = len(w)
                    if score > best_score:
                        best_score = score
                        best_match = proj
                        
    if best_match:
        logger.info(f"🎯 Projet détecté via acronyme ou client : {best_match} (score={best_score})")
        return best_match
        
    return None