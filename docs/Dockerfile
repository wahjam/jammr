FROM python:3.13.2-alpine3.21
RUN pip install mkdocs
ENTRYPOINT ["mkdocs"]
CMD ["serve", "--dev-addr", "0.0.0.0:8000"]
EXPOSE 8000
VOLUME ["/docs"]
WORKDIR /docs
