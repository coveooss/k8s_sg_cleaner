FROM python:3

ADD check_k8s_sg.py /

RUN pip install boto3 click kubernetes

CMD [ "python", "./check_k8s_sg.py" ]