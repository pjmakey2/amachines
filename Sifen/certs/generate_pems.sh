#!/bin/bash
#..f1kdrM33T0kn..
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -out sifen_aco.nokey.pem -nokeys
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -out sifen_aco.withkey.pem
# openssl rsa -in sifen_aco.withkey.pem -out sifen_aco.key
# cat sifen_aco.nokey.pem sifen_aco.key > sifen_aco.combo.pem
#To convert a PFX file to a PEM file that contains both the certificate and private key, the following command needs to be used:
#Extract the private key with the certificate
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -out sifen_aco_private_cert.pem -nodes

# # Exporting the certificate only:
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -clcerts -nokeys -out sifen_aco.pem
# # Removing the password from the extracted private key:
# openssl rsa -in sifen_aco_key.pem -out sifen_aco_server.key
# #extract the private key
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -nocerts -nodes -out sifen_aco_private_key.cer
# # Extra the CA Certificate
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -cacerts -nokeys -chain -out sifen_aco_ca.cer

# #Extract the KEY
# #openssl pkcs12 -in 20231025_aconcagua_cert.pfx -clcerts -nokeys -out sifen_aco.pem
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -nocerts -out sifen_aco.pem
# openssl pkcs12 -in 20231025_aconcagua_cert.pfx -nocerts -nodes -out sifen_aco.key
# # Conversion to separate PEM files
# # We can extract the private key form a PFX to a PEM file with this command:

# # Extra the public KEY
# openssl rsa -in sifen_aco.key -pubout -out sifen_aco.pub
#New method for Toca3d
rm -vf toca3d.key
openssl pkcs12 -legacy -in toca3d.pfx -out toca3d.key -nocerts -nodes -password pass:acot5202
rm -vf toca3d.pem
openssl pkcs12 -legacy -in toca3d.pfx -out toca3d.pem -nokeys -clcerts -password pass:acot5202
#You should open the .pem and .key file to get rip of unnecessary info
