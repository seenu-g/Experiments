/*eslint-disable block-scoped-var, id-length, no-control-regex, no-magic-numbers, no-prototype-builtins, no-redeclare, no-shadow, no-var, sort-vars*/
"use strict";

var $protobuf = require("protobufjs/minimal");

// Common aliases
var $Reader = $protobuf.Reader, $Writer = $protobuf.Writer, $util = $protobuf.util;

// Exported root namespace
var $root = $protobuf.roots["default"] || ($protobuf.roots["default"] = {});

$root.demo = (function() {

    /**
     * Namespace demo.
     * @exports demo
     * @namespace
     */
    var demo = {};

    demo.People = (function() {

        /**
         * Properties of a People.
         * @memberof demo
         * @interface IPeople
         * @property {Array.<demo.IPerson>|null} [person] People person
         */

        /**
         * Constructs a new People.
         * @memberof demo
         * @classdesc Represents a People.
         * @implements IPeople
         * @constructor
         * @param {demo.IPeople=} [properties] Properties to set
         */
        function People(properties) {
            this.person = [];
            if (properties)
                for (var keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                    if (properties[keys[i]] != null)
                        this[keys[i]] = properties[keys[i]];
        }

        /**
         * People person.
         * @member {Array.<demo.IPerson>} person
         * @memberof demo.People
         * @instance
         */
        People.prototype.person = $util.emptyArray;

        /**
         * Creates a new People instance using the specified properties.
         * @function create
         * @memberof demo.People
         * @static
         * @param {demo.IPeople=} [properties] Properties to set
         * @returns {demo.People} People instance
         */
        People.create = function create(properties) {
            return new People(properties);
        };

        /**
         * Encodes the specified People message. Does not implicitly {@link demo.People.verify|verify} messages.
         * @function encode
         * @memberof demo.People
         * @static
         * @param {demo.IPeople} message People message or plain object to encode
         * @param {$protobuf.Writer} [writer] Writer to encode to
         * @returns {$protobuf.Writer} Writer
         */
        People.encode = function encode(message, writer) {
            if (!writer)
                writer = $Writer.create();
            if (message.person != null && message.person.length)
                for (var i = 0; i < message.person.length; ++i)
                    $root.demo.Person.encode(message.person[i], writer.uint32(/* id 1, wireType 2 =*/10).fork()).ldelim();
            return writer;
        };

        /**
         * Encodes the specified People message, length delimited. Does not implicitly {@link demo.People.verify|verify} messages.
         * @function encodeDelimited
         * @memberof demo.People
         * @static
         * @param {demo.IPeople} message People message or plain object to encode
         * @param {$protobuf.Writer} [writer] Writer to encode to
         * @returns {$protobuf.Writer} Writer
         */
        People.encodeDelimited = function encodeDelimited(message, writer) {
            return this.encode(message, writer).ldelim();
        };

        /**
         * Decodes a People message from the specified reader or buffer.
         * @function decode
         * @memberof demo.People
         * @static
         * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
         * @param {number} [length] Message length if known beforehand
         * @returns {demo.People} People
         * @throws {Error} If the payload is not a reader or valid buffer
         * @throws {$protobuf.util.ProtocolError} If required fields are missing
         */
        People.decode = function decode(reader, length) {
            if (!(reader instanceof $Reader))
                reader = $Reader.create(reader);
            var end = length === undefined ? reader.len : reader.pos + length, message = new $root.demo.People();
            while (reader.pos < end) {
                var tag = reader.uint32();
                switch (tag >>> 3) {
                case 1:
                    if (!(message.person && message.person.length))
                        message.person = [];
                    message.person.push($root.demo.Person.decode(reader, reader.uint32()));
                    break;
                default:
                    reader.skipType(tag & 7);
                    break;
                }
            }
            return message;
        };

        /**
         * Decodes a People message from the specified reader or buffer, length delimited.
         * @function decodeDelimited
         * @memberof demo.People
         * @static
         * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
         * @returns {demo.People} People
         * @throws {Error} If the payload is not a reader or valid buffer
         * @throws {$protobuf.util.ProtocolError} If required fields are missing
         */
        People.decodeDelimited = function decodeDelimited(reader) {
            if (!(reader instanceof $Reader))
                reader = new $Reader(reader);
            return this.decode(reader, reader.uint32());
        };

        /**
         * Verifies a People message.
         * @function verify
         * @memberof demo.People
         * @static
         * @param {Object.<string,*>} message Plain object to verify
         * @returns {string|null} `null` if valid, otherwise the reason why it is not
         */
        People.verify = function verify(message) {
            if (typeof message !== "object" || message === null)
                return "object expected";
            if (message.person != null && message.hasOwnProperty("person")) {
                if (!Array.isArray(message.person))
                    return "person: array expected";
                for (var i = 0; i < message.person.length; ++i) {
                    var error = $root.demo.Person.verify(message.person[i]);
                    if (error)
                        return "person." + error;
                }
            }
            return null;
        };

        /**
         * Creates a People message from a plain object. Also converts values to their respective internal types.
         * @function fromObject
         * @memberof demo.People
         * @static
         * @param {Object.<string,*>} object Plain object
         * @returns {demo.People} People
         */
        People.fromObject = function fromObject(object) {
            if (object instanceof $root.demo.People)
                return object;
            var message = new $root.demo.People();
            if (object.person) {
                if (!Array.isArray(object.person))
                    throw TypeError(".demo.People.person: array expected");
                message.person = [];
                for (var i = 0; i < object.person.length; ++i) {
                    if (typeof object.person[i] !== "object")
                        throw TypeError(".demo.People.person: object expected");
                    message.person[i] = $root.demo.Person.fromObject(object.person[i]);
                }
            }
            return message;
        };

        /**
         * Creates a plain object from a People message. Also converts values to other types if specified.
         * @function toObject
         * @memberof demo.People
         * @static
         * @param {demo.People} message People
         * @param {$protobuf.IConversionOptions} [options] Conversion options
         * @returns {Object.<string,*>} Plain object
         */
        People.toObject = function toObject(message, options) {
            if (!options)
                options = {};
            var object = {};
            if (options.arrays || options.defaults)
                object.person = [];
            if (message.person && message.person.length) {
                object.person = [];
                for (var j = 0; j < message.person.length; ++j)
                    object.person[j] = $root.demo.Person.toObject(message.person[j], options);
            }
            return object;
        };

        /**
         * Converts this People to JSON.
         * @function toJSON
         * @memberof demo.People
         * @instance
         * @returns {Object.<string,*>} JSON object
         */
        People.prototype.toJSON = function toJSON() {
            return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
        };

        return People;
    })();

    demo.Person = (function() {

        /**
         * Properties of a Person.
         * @memberof demo
         * @interface IPerson
         * @property {string|null} [name] Person name
         * @property {Array.<demo.IAddress>|null} [address] Person address
         * @property {Array.<string>|null} [mobile] Person mobile
         * @property {Array.<string>|null} [email] Person email
         */

        /**
         * Constructs a new Person.
         * @memberof demo
         * @classdesc Represents a Person.
         * @implements IPerson
         * @constructor
         * @param {demo.IPerson=} [properties] Properties to set
         */
        function Person(properties) {
            this.address = [];
            this.mobile = [];
            this.email = [];
            if (properties)
                for (var keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                    if (properties[keys[i]] != null)
                        this[keys[i]] = properties[keys[i]];
        }

        /**
         * Person name.
         * @member {string} name
         * @memberof demo.Person
         * @instance
         */
        Person.prototype.name = "";

        /**
         * Person address.
         * @member {Array.<demo.IAddress>} address
         * @memberof demo.Person
         * @instance
         */
        Person.prototype.address = $util.emptyArray;

        /**
         * Person mobile.
         * @member {Array.<string>} mobile
         * @memberof demo.Person
         * @instance
         */
        Person.prototype.mobile = $util.emptyArray;

        /**
         * Person email.
         * @member {Array.<string>} email
         * @memberof demo.Person
         * @instance
         */
        Person.prototype.email = $util.emptyArray;

        /**
         * Creates a new Person instance using the specified properties.
         * @function create
         * @memberof demo.Person
         * @static
         * @param {demo.IPerson=} [properties] Properties to set
         * @returns {demo.Person} Person instance
         */
        Person.create = function create(properties) {
            return new Person(properties);
        };

        /**
         * Encodes the specified Person message. Does not implicitly {@link demo.Person.verify|verify} messages.
         * @function encode
         * @memberof demo.Person
         * @static
         * @param {demo.IPerson} message Person message or plain object to encode
         * @param {$protobuf.Writer} [writer] Writer to encode to
         * @returns {$protobuf.Writer} Writer
         */
        Person.encode = function encode(message, writer) {
            if (!writer)
                writer = $Writer.create();
            if (message.name != null && message.hasOwnProperty("name"))
                writer.uint32(/* id 1, wireType 2 =*/10).string(message.name);
            if (message.address != null && message.address.length)
                for (var i = 0; i < message.address.length; ++i)
                    $root.demo.Address.encode(message.address[i], writer.uint32(/* id 2, wireType 2 =*/18).fork()).ldelim();
            if (message.mobile != null && message.mobile.length)
                for (var i = 0; i < message.mobile.length; ++i)
                    writer.uint32(/* id 3, wireType 2 =*/26).string(message.mobile[i]);
            if (message.email != null && message.email.length)
                for (var i = 0; i < message.email.length; ++i)
                    writer.uint32(/* id 4, wireType 2 =*/34).string(message.email[i]);
            return writer;
        };

        /**
         * Encodes the specified Person message, length delimited. Does not implicitly {@link demo.Person.verify|verify} messages.
         * @function encodeDelimited
         * @memberof demo.Person
         * @static
         * @param {demo.IPerson} message Person message or plain object to encode
         * @param {$protobuf.Writer} [writer] Writer to encode to
         * @returns {$protobuf.Writer} Writer
         */
        Person.encodeDelimited = function encodeDelimited(message, writer) {
            return this.encode(message, writer).ldelim();
        };

        /**
         * Decodes a Person message from the specified reader or buffer.
         * @function decode
         * @memberof demo.Person
         * @static
         * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
         * @param {number} [length] Message length if known beforehand
         * @returns {demo.Person} Person
         * @throws {Error} If the payload is not a reader or valid buffer
         * @throws {$protobuf.util.ProtocolError} If required fields are missing
         */
        Person.decode = function decode(reader, length) {
            if (!(reader instanceof $Reader))
                reader = $Reader.create(reader);
            var end = length === undefined ? reader.len : reader.pos + length, message = new $root.demo.Person();
            while (reader.pos < end) {
                var tag = reader.uint32();
                switch (tag >>> 3) {
                case 1:
                    message.name = reader.string();
                    break;
                case 2:
                    if (!(message.address && message.address.length))
                        message.address = [];
                    message.address.push($root.demo.Address.decode(reader, reader.uint32()));
                    break;
                case 3:
                    if (!(message.mobile && message.mobile.length))
                        message.mobile = [];
                    message.mobile.push(reader.string());
                    break;
                case 4:
                    if (!(message.email && message.email.length))
                        message.email = [];
                    message.email.push(reader.string());
                    break;
                default:
                    reader.skipType(tag & 7);
                    break;
                }
            }
            return message;
        };

        /**
         * Decodes a Person message from the specified reader or buffer, length delimited.
         * @function decodeDelimited
         * @memberof demo.Person
         * @static
         * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
         * @returns {demo.Person} Person
         * @throws {Error} If the payload is not a reader or valid buffer
         * @throws {$protobuf.util.ProtocolError} If required fields are missing
         */
        Person.decodeDelimited = function decodeDelimited(reader) {
            if (!(reader instanceof $Reader))
                reader = new $Reader(reader);
            return this.decode(reader, reader.uint32());
        };

        /**
         * Verifies a Person message.
         * @function verify
         * @memberof demo.Person
         * @static
         * @param {Object.<string,*>} message Plain object to verify
         * @returns {string|null} `null` if valid, otherwise the reason why it is not
         */
        Person.verify = function verify(message) {
            if (typeof message !== "object" || message === null)
                return "object expected";
            if (message.name != null && message.hasOwnProperty("name"))
                if (!$util.isString(message.name))
                    return "name: string expected";
            if (message.address != null && message.hasOwnProperty("address")) {
                if (!Array.isArray(message.address))
                    return "address: array expected";
                for (var i = 0; i < message.address.length; ++i) {
                    var error = $root.demo.Address.verify(message.address[i]);
                    if (error)
                        return "address." + error;
                }
            }
            if (message.mobile != null && message.hasOwnProperty("mobile")) {
                if (!Array.isArray(message.mobile))
                    return "mobile: array expected";
                for (var i = 0; i < message.mobile.length; ++i)
                    if (!$util.isString(message.mobile[i]))
                        return "mobile: string[] expected";
            }
            if (message.email != null && message.hasOwnProperty("email")) {
                if (!Array.isArray(message.email))
                    return "email: array expected";
                for (var i = 0; i < message.email.length; ++i)
                    if (!$util.isString(message.email[i]))
                        return "email: string[] expected";
            }
            return null;
        };

        /**
         * Creates a Person message from a plain object. Also converts values to their respective internal types.
         * @function fromObject
         * @memberof demo.Person
         * @static
         * @param {Object.<string,*>} object Plain object
         * @returns {demo.Person} Person
         */
        Person.fromObject = function fromObject(object) {
            if (object instanceof $root.demo.Person)
                return object;
            var message = new $root.demo.Person();
            if (object.name != null)
                message.name = String(object.name);
            if (object.address) {
                if (!Array.isArray(object.address))
                    throw TypeError(".demo.Person.address: array expected");
                message.address = [];
                for (var i = 0; i < object.address.length; ++i) {
                    if (typeof object.address[i] !== "object")
                        throw TypeError(".demo.Person.address: object expected");
                    message.address[i] = $root.demo.Address.fromObject(object.address[i]);
                }
            }
            if (object.mobile) {
                if (!Array.isArray(object.mobile))
                    throw TypeError(".demo.Person.mobile: array expected");
                message.mobile = [];
                for (var i = 0; i < object.mobile.length; ++i)
                    message.mobile[i] = String(object.mobile[i]);
            }
            if (object.email) {
                if (!Array.isArray(object.email))
                    throw TypeError(".demo.Person.email: array expected");
                message.email = [];
                for (var i = 0; i < object.email.length; ++i)
                    message.email[i] = String(object.email[i]);
            }
            return message;
        };

        /**
         * Creates a plain object from a Person message. Also converts values to other types if specified.
         * @function toObject
         * @memberof demo.Person
         * @static
         * @param {demo.Person} message Person
         * @param {$protobuf.IConversionOptions} [options] Conversion options
         * @returns {Object.<string,*>} Plain object
         */
        Person.toObject = function toObject(message, options) {
            if (!options)
                options = {};
            var object = {};
            if (options.arrays || options.defaults) {
                object.address = [];
                object.mobile = [];
                object.email = [];
            }
            if (options.defaults)
                object.name = "";
            if (message.name != null && message.hasOwnProperty("name"))
                object.name = message.name;
            if (message.address && message.address.length) {
                object.address = [];
                for (var j = 0; j < message.address.length; ++j)
                    object.address[j] = $root.demo.Address.toObject(message.address[j], options);
            }
            if (message.mobile && message.mobile.length) {
                object.mobile = [];
                for (var j = 0; j < message.mobile.length; ++j)
                    object.mobile[j] = message.mobile[j];
            }
            if (message.email && message.email.length) {
                object.email = [];
                for (var j = 0; j < message.email.length; ++j)
                    object.email[j] = message.email[j];
            }
            return object;
        };

        /**
         * Converts this Person to JSON.
         * @function toJSON
         * @memberof demo.Person
         * @instance
         * @returns {Object.<string,*>} JSON object
         */
        Person.prototype.toJSON = function toJSON() {
            return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
        };

        return Person;
    })();

    demo.Address = (function() {

        /**
         * Properties of an Address.
         * @memberof demo
         * @interface IAddress
         * @property {string|null} [street] Address street
         * @property {number|null} [number] Address number
         */

        /**
         * Constructs a new Address.
         * @memberof demo
         * @classdesc Represents an Address.
         * @implements IAddress
         * @constructor
         * @param {demo.IAddress=} [properties] Properties to set
         */
        function Address(properties) {
            if (properties)
                for (var keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                    if (properties[keys[i]] != null)
                        this[keys[i]] = properties[keys[i]];
        }

        /**
         * Address street.
         * @member {string} street
         * @memberof demo.Address
         * @instance
         */
        Address.prototype.street = "";

        /**
         * Address number.
         * @member {number} number
         * @memberof demo.Address
         * @instance
         */
        Address.prototype.number = 0;

        /**
         * Creates a new Address instance using the specified properties.
         * @function create
         * @memberof demo.Address
         * @static
         * @param {demo.IAddress=} [properties] Properties to set
         * @returns {demo.Address} Address instance
         */
        Address.create = function create(properties) {
            return new Address(properties);
        };

        /**
         * Encodes the specified Address message. Does not implicitly {@link demo.Address.verify|verify} messages.
         * @function encode
         * @memberof demo.Address
         * @static
         * @param {demo.IAddress} message Address message or plain object to encode
         * @param {$protobuf.Writer} [writer] Writer to encode to
         * @returns {$protobuf.Writer} Writer
         */
        Address.encode = function encode(message, writer) {
            if (!writer)
                writer = $Writer.create();
            if (message.street != null && message.hasOwnProperty("street"))
                writer.uint32(/* id 1, wireType 2 =*/10).string(message.street);
            if (message.number != null && message.hasOwnProperty("number"))
                writer.uint32(/* id 2, wireType 0 =*/16).int32(message.number);
            return writer;
        };

        /**
         * Encodes the specified Address message, length delimited. Does not implicitly {@link demo.Address.verify|verify} messages.
         * @function encodeDelimited
         * @memberof demo.Address
         * @static
         * @param {demo.IAddress} message Address message or plain object to encode
         * @param {$protobuf.Writer} [writer] Writer to encode to
         * @returns {$protobuf.Writer} Writer
         */
        Address.encodeDelimited = function encodeDelimited(message, writer) {
            return this.encode(message, writer).ldelim();
        };

        /**
         * Decodes an Address message from the specified reader or buffer.
         * @function decode
         * @memberof demo.Address
         * @static
         * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
         * @param {number} [length] Message length if known beforehand
         * @returns {demo.Address} Address
         * @throws {Error} If the payload is not a reader or valid buffer
         * @throws {$protobuf.util.ProtocolError} If required fields are missing
         */
        Address.decode = function decode(reader, length) {
            if (!(reader instanceof $Reader))
                reader = $Reader.create(reader);
            var end = length === undefined ? reader.len : reader.pos + length, message = new $root.demo.Address();
            while (reader.pos < end) {
                var tag = reader.uint32();
                switch (tag >>> 3) {
                case 1:
                    message.street = reader.string();
                    break;
                case 2:
                    message.number = reader.int32();
                    break;
                default:
                    reader.skipType(tag & 7);
                    break;
                }
            }
            return message;
        };

        /**
         * Decodes an Address message from the specified reader or buffer, length delimited.
         * @function decodeDelimited
         * @memberof demo.Address
         * @static
         * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
         * @returns {demo.Address} Address
         * @throws {Error} If the payload is not a reader or valid buffer
         * @throws {$protobuf.util.ProtocolError} If required fields are missing
         */
        Address.decodeDelimited = function decodeDelimited(reader) {
            if (!(reader instanceof $Reader))
                reader = new $Reader(reader);
            return this.decode(reader, reader.uint32());
        };

        /**
         * Verifies an Address message.
         * @function verify
         * @memberof demo.Address
         * @static
         * @param {Object.<string,*>} message Plain object to verify
         * @returns {string|null} `null` if valid, otherwise the reason why it is not
         */
        Address.verify = function verify(message) {
            if (typeof message !== "object" || message === null)
                return "object expected";
            if (message.street != null && message.hasOwnProperty("street"))
                if (!$util.isString(message.street))
                    return "street: string expected";
            if (message.number != null && message.hasOwnProperty("number"))
                if (!$util.isInteger(message.number))
                    return "number: integer expected";
            return null;
        };

        /**
         * Creates an Address message from a plain object. Also converts values to their respective internal types.
         * @function fromObject
         * @memberof demo.Address
         * @static
         * @param {Object.<string,*>} object Plain object
         * @returns {demo.Address} Address
         */
        Address.fromObject = function fromObject(object) {
            if (object instanceof $root.demo.Address)
                return object;
            var message = new $root.demo.Address();
            if (object.street != null)
                message.street = String(object.street);
            if (object.number != null)
                message.number = object.number | 0;
            return message;
        };

        /**
         * Creates a plain object from an Address message. Also converts values to other types if specified.
         * @function toObject
         * @memberof demo.Address
         * @static
         * @param {demo.Address} message Address
         * @param {$protobuf.IConversionOptions} [options] Conversion options
         * @returns {Object.<string,*>} Plain object
         */
        Address.toObject = function toObject(message, options) {
            if (!options)
                options = {};
            var object = {};
            if (options.defaults) {
                object.street = "";
                object.number = 0;
            }
            if (message.street != null && message.hasOwnProperty("street"))
                object.street = message.street;
            if (message.number != null && message.hasOwnProperty("number"))
                object.number = message.number;
            return object;
        };

        /**
         * Converts this Address to JSON.
         * @function toJSON
         * @memberof demo.Address
         * @instance
         * @returns {Object.<string,*>} JSON object
         */
        Address.prototype.toJSON = function toJSON() {
            return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
        };

        return Address;
    })();

    return demo;
})();

module.exports = $root;
