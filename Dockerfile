# Base image
FROM python:3.7-slim

# Set environment variables
# https://docs.python.org/3/using/cmdline.html#environment-variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file to the working directory
COPY requirements.txt /code/

#RUN apt-get update && apt-get upgrade -y && apt-get install -y \
#    zlib1g-dev libjpeg-dev
#    libtiff-dev libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev tcl8.6-dev tk8.6-dev python3-tk

# Install project dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project code to the working directory
COPY . /code/

# Expose port 8000 for the Django development server
EXPOSE 8000

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]