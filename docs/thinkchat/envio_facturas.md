Testing thinkchat.
https://fl.altamachines.com:8000/media/rpt/304880676235885765570421322560320449379.pdf

Cliente: thinkchat
Linea: 595992733111

Token: tk-1dbc29d73f836a627814fae293f88b533b83397507abad912054114a269-

curl -H "Authorization: Bearer tk-1dbc29d73f836a627814fae293f88b533b83397507abad912054114a269-" --location -g 'https://thinkchat.whatsapp.net.py/thinkcomm-x/api/v2/' \
--data '{
    "action": "get_templates",
    "from": "595992733111"
}'

curl -H "Authorization: Bearer tk-1dbc29d73f836a627814fae293f88b533b83397507abad912054114a269-" --location -g 'https://thinkchat.whatsapp.net.py/thinkcomm-x/api/v2/' \
--data '{
    "action": "send_template",
    "from": "595992733111",
    "to": "595985299866",
    "template_id": "1480190397116993",
    "template_params": ["PJL"],
    "template_media": "https://fl.altamachines.com:8000/media/rpt/304880676235885765570421322560320449379.pdf",
    "extras": {
        "inbound_bot": 4
    }
}'