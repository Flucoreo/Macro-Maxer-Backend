FROM python:3.13.1-slim

WORKDIR /code

# install redis
# RUN apt-get update && apt-get install -y redis-server

COPY ./requirements.txt /code/requirements.txt

# install python package requiremetns
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./run_app.sh /code/run_app.sh

EXPOSE 8000

CMD ["bash", "run_app.sh"]