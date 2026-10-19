# pharmaflow-AI

This repository hosts **DOCUPRO — Smart Document Converter**, a complete,
self-hostable document conversion product.

* Web application + conversion API: [`docupro/`](docupro/)
* Documentation: [`docupro/docs/`](docupro/docs/)
* Quick start: [`docupro/README.md`](docupro/README.md)

```bash
cd docupro
cp .env.example .env
docker compose up -d --build     # interface on http://localhost:8000
```

No account, no database and no third-party conversion API is involved: the
service converts documents on your own infrastructure and deletes them
automatically.
