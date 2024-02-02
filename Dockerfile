FROM python
ADD main.py .
RUN pip install --upgrade pip
RUN pip install requests email python-telegram-bot schedule --pre
ADD config.py .
CMD ["python", "main.py"]
# Or enter the name of your unique directory and parameter set.