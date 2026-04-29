{
    "name": "Demandes Curyeux",
    "version": "1.0",
    "summary": "Gestion des demandes internes pour les succursales de Curyeux",
    "author": "Curyeux",
    "website": "https://shop.curyeux.net",
    "category": "Operations",
    "depends": ["base"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menus.xml",
        "views/request_views.xml",
        "views/request_line_views.xml",
        "views/branch_views.xml",
        "views/product_views.xml",
        "report/report_views.xml"
    ],
    "images": ["static/description/icon.png"],
    "installable": True,
    "application": True,
    "license": "LGPL-3"
}
