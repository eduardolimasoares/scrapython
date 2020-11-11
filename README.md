# How to use this image
This image is designed to be used in a container crawler.

## Create the image
From the root folder, run the command

```console
$ docker build -t scrapython .
```

## Run the container
You can pass the parameters to the container when running it.

```console
$ cat websites.txt | docker run -i --rm scrapython
```
