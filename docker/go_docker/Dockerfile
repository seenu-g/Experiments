FROM golang:1.12.0-alpine3.9
# create an /app directory within our image that will hold our application source files
RUN mkdir /app
# copy everything in the root directory into our /app directory
ADD . /app
# Specify that any further commands will be executed inside our /app directory
WORKDIR /app
# Run go build to compile the binary executable of our Go program
RUN go build -o main .
# start command which kicks off newly created binary executable
CMD ["/app/main"]