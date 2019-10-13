from django.shortcuts import render, HttpResponse
from app.tests import detect_image
from app.forms import UploadFileForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.conf import settings



# Create your views here.
def main(request):

    context = {"type" : "search", "fname" : ""}

    return render(request, "index.html", context)



def detect(request):

    if request.method == "POST":

        # remove existing files
        default_storage.delete("upload/original.jpg")
        default_storage.delete("result/result.jpg")
        default_storage.delete("upload/original.png")
        default_storage.delete("result/result.png")

        # get uploaded file
        file = request.FILES['file01']
        print("file name :", file.name)
        file_type = file.name.split(".")[-1]

        # save original image
        path = default_storage.save("upload/original.{file_type}".format(file_type = file_type ),
                                    ContentFile(file.read()))

        f_absolute_path = os.path.join(settings.MEDIA_ROOT, path)

        # run detection and save detected image
        detected_categories, detection_scores = detect_image(f_absolute_path)

        if detected_categories == None :
            context = {"type" : "error", "fname" : file.name, "detected_categories" : detected_categories, "detection_scores" : detection_scores}
        else :
            context = {"type" : "result", "fname" : file.name, "detected_categories" : detected_categories, "detection_scores" : detection_scores}

        return render(request, "index.html", context)