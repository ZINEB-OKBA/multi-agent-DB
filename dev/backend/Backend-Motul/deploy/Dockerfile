FROM eclipse-temurin:17-jdk
COPY *.jar app.jar

RUN mkdir -p /opt/deploy/capital-trust
RUN mkdir -p /opt/deploy/capital-trust/resources

EXPOSE 8081
ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom","-Dspring.profiles.active=cloud","-jar","app.jar"]