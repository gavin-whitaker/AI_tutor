FROM eclipse-temurin:21-jdk

WORKDIR /sandbox

COPY run_java.sh /run_java.sh
RUN chmod +x /run_java.sh

CMD ["/run_java.sh"]
