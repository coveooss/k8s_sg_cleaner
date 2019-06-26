FROM python:3-alpine

ADD check_k8s_sg.py /

RUN pip install boto3 click kubernetes

ENTRYPOINT [ "python", "./check_k8s_sg.py" ]
CMD [ "" ]