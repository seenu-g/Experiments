Generate js from proto to compile project

npm install protobufjs


node_modules/protobufjs/cli/bin/pbjs -t static-module -w commonjs -o kyc.js kyc.proto
node_modules/protobufjs/cli/bin/pbts -o kyc.d.ts kyc.js

// if permission error
//sudo chmod 755 node_modules/protobufjs/cli/bin/pbjs
//sudo chmod 755 node_modules/protobufjs/cli/bin/pbts