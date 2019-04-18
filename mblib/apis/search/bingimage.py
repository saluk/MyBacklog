from azure.cognitiveservices.search.imagesearch import ImageSearchAPI
from msrest.authentication import CognitiveServicesCredentials

subscription_key = "0be08b35f8174bec9fe33f86ce9382f2"
search_term = "tear for vermillion"

"""
This application will search images on the web with the Bing Image Search API and print out first image result.
"""
#create the image search client
client = ImageSearchAPI(CognitiveServicesCredentials(subscription_key))

def get_images(search_term, count=10):
    image_results = client.images.search(query=search_term)
    li = []
    for image in image_results.value:
        li.append((image.thumbnail_url, image.content_url))
    return li

if __name__=="__main__":
    image_results = client.images.search(query=search_term)
    print("Searching the web for images of: {}".format(search_term))

    # Image results
    if image_results.value:
        first_image_result = image_results.value[0]
        print("Total number of images returned: {}".format(len(image_results.value)))
        print("First image thumbnail url: {}".format(
            first_image_result.thumbnail_url))
        print("First image content url: {}".format(first_image_result.content_url))
    else:
        print("Couldn't find image results!")
