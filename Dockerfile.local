FROM python:3.9-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050
CMD ["python", "docscope/app.py"]

#sudo systemctl restart docker
#docker system prune -a --volumes
#echo "chromadb_last/" > .dockerignore #(I need to use this if the driver is large. It will not use it during the time that it builds it.)

#docker run -p 8501:8501 -v /home/ubuntu/Second_Attempt/chromadb_last:/app/chromadb_last china_chat

#df -h
#docker build -t my_dash_app .
#docker run -d -p 8050:8050 my_dash_app

#Debugging:
    #docker ps -a
    # docker logs <docker_name>