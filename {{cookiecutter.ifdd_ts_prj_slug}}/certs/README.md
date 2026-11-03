# CA certificates for Grafana

Put the certificate of every CA that signed a server Grafana calls itself
here, as PEM files (`*.crt` or `*.pem`, one or several certificates each;
for an intermediate CA a bundle of root and intermediate): the realm for the
login (token, keys) and the backend for the data sources, in particular when
they run on another server with a CA of its own.

The directory is mounted read-only into Grafana and added to its trust store
through `SSL_CERT_DIR`, next to the system CAs. Grafana runs as UID 472, so
the files must be readable for others (mode 0644). Restart Grafana after a
change. No private keys here: everything in this directory is read as a
certificate.
