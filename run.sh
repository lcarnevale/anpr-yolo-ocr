docker run -d --name platedetection \
    -v /var/log/platedetection:/opt/app/log \
    -v ~/static-files:/opt/app/static-files \
    lcarnevale/platedetection