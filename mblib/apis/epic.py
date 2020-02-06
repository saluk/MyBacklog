import requests

search_str = {
    "query":"\n            query catalogQuery(\n                $category:String,\n                $count:Int,\n                $country:String!,\n                $keywords: String,\n                $locale:String,\n                $namespace:String!,\n                $sortBy:String,\n                $sortDir:String,\n                $start:Int,\n                $tag:String\n            ) {\n                Catalog {\n                    catalogOffers(\n                        namespace: $namespace,\n                        locale: $locale,\n                        params: {\n                            count: $count,\n                            country: $country,\n                            category: $category,\n                            keywords: $keywords,\n                            sortBy: $sortBy,\n                            sortDir: $sortDir,\n                            start: $start,\n                            tag: $tag\n                        }\n                    ) {\n                        elements {\n                            isFeatured\n                            collectionOfferIds\n                            \n          title\n          id\n          namespace\n          description\n          keyImages {\n            type\n            url\n          }\n          seller {\n              id\n              name\n          }\n          productSlug\n          urlSlug\n          items {\n            id\n            namespace\n          }\n          customAttributes {\n            key\n            value\n          }\n          categories {\n            path\n          }\n          price(country: $country) {\n            totalPrice {\n              discountPrice\n              originalPrice\n              voucherDiscount\n              discount\n              fmtPrice(locale: $locale) {\n                originalPrice\n                discountPrice\n                intermediatePrice\n              }\n            }\n            lineOffers {\n              appliedRules {\n                id\n                endDate\n              }\n            }\n          }\n          linkedOfferId\n          linkedOffer {\n            effectiveDate\n            customAttributes {\n              key\n              value\n            }\n          }\n        \n                        }\n                        paging {\n                            count,\n                            total\n                        }\n                    }\n                }\n            }\n        ",
    "variables":{
        "category":"games|bundles|engines",
        "count":30,
        "country":"US",
        "keywords":"",
        "locale":"en-US",
        "namespace":"epic",
        "sortBy":None,
        "sortDir":"DESC",
        "start":0,
        "tag":""
    }
}

def find_screenshot(game_name):
    search_str["variables"]["keywords"] = game_name
    r = requests.post("https://graphql.epicgames.com/graphql", json=search_str)
    j = r.json()
    images = []
    for item in j["data"]["Catalog"]["catalogOffers"]["elements"]:
        images.append(item["keyImages"][0])
    sort_by = ["DieselStoreFrontTall", "DieselStoreFrontWide", "DieselGameBoxLogo"]
    images.sort(key=lambda img: sort_by.index(img["type"]) if img["type"] in sort_by else 99)
    return images[0]["url"]

print(find_screenshot("Oxenfree"))