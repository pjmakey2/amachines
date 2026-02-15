#!/bin/bash
# Script desactualizado - usar generate_pems.sh en su lugar
openssl pkcs12 -legacy -in toca3d.pfx -out toca3d.pem -clcerts -nokeys -password pass:acot5202
openssl pkcs12 -legacy -in toca3d.pfx -out toca3d.key -nocerts -nodes -password pass:acot5202