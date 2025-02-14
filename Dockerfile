FROM python
ADD main.py .
RUN pip install --upgrade pip
RUN pip install requests email python-telegram-bot schedule nextcloud-api-wrapper webdavclient3 --pre
ADD config.py .
CMD ["python", "main.py"]
