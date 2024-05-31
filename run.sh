docker run -d --name platedetection -p 8080:8080\
    -v /var/log/platedetection:/opt/app/log \
    -v ~/static-files:/opt/app/static-files \
    platedetection