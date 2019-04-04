npm install protobufjs

//convert your .proto files into standard CommonJs modules to import in your Node.js backend
node_modules/protobufjs/cli/bin/pbjs -t static-module -w commonjs -o record.js record.proto
node_modules/protobufjs/cli/bin/pbjs -t static-module -w commonjs -o agent.js agent.proto

//To generate the typescript declaration file
node_modules/protobufjs/cli/bin/pbts -o agent.d.ts agent.js
node_modules/protobufjs/cli/bin/pbts -o record.d.ts record.js
//agent.js is file generated in the previous step and not the original model.proto.
//you will need both files in your frontend app

// if there are multiple. proto files, there is possibility to merge them in to one.
npm install -g browserify
browserify people.js agent.js record.js -o bundle.js

// if you see error "EACCES: permission denied", run this command
sudo chmod 755 node_modules/protobufjs/cli/bin/pbjs
sudo chmod 755 node_modules/protobufjs/cli/bin/pbts

