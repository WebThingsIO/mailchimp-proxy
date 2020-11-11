FROM python:3.9

COPY mailchimp-proxy.py requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

ENTRYPOINT ["/app/mailchimp-proxy.py"]
