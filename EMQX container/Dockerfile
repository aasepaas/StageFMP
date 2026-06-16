FROM emqx/emqx:5.10.3

USER root

# Voeg jouw EJBCA CA toe aan trusted store
COPY certs/ManagementCA.pem /usr/local/share/ca-certificates/ejbca-ca.crt

# Installeer CA in trust store
RUN update-ca-certificates

USER emqx