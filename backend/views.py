from django.shortcuts import render
import random
from rest_framework import permissions, viewsets, mixins
from rest_framework import status
from django.http import JsonResponse
import backend.models as app_models
import backend.serializers as app_serializers


def index(request):
    return render(request, 'index.html')


class DialogueViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)

    queryset = app_models.Dialogues.objects.all()

    def get_dialogues(self, request, *args, **kwargs):

        # Get All Parameters
        try:
            limit = int(request.GET["limit"])
            remove_dialogues = request.GET["remove-dialogues"].split(',')
        except:
            return JsonResponse({"error": "Bad Parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Set Start year
            start_year = 1980

            # Get all dialogues and remove old dialogues
            dialogue_objects = self.queryset.filter(movie_year__gte=start_year).exclude(id__in=remove_dialogues)

            # Check limit
            if limit == 1:
                dialogue = random.choice(dialogue_objects)
                dialogue_ser = app_serializers.DialogueSerializer(dialogue)
                return JsonResponse({"dialogue": dialogue_ser.data}, status=status.HTTP_200_OK)
            elif limit > 1:
                dialogues = []
                while limit != 0:
                    dialogues.append(random.choice(dialogue_objects))
                    limit -= 1
                dialogues_ser = app_serializers.DialogueSerializer(dialogues, many=True)
                return JsonResponse({"dialogues": dialogues_ser.data}, status=status.HTTP_200_OK)
        except:
            return JsonResponse({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def add_emoji(self, request, *args, **kwargs):

        # Get All Parameters
        try:
            dialogue = request.data["dialogue"]
            mood = request.data["mood"]
        except:
            return JsonResponse({"error": "Bad Parameters"}, status=status.HTTP_400_BAD_REQUEST)

        # Check If Emotion is present
        dialogue_obj = app_models.Dialogues.objects.get(id=dialogue)
        emotion_objects = app_models.Emotion.objects.filter(mood=mood, dialogue=dialogue_obj)
        if len(emotion_objects) == 0:
            emotion_object = app_models.Emotion.objects.create(mood=mood, dialogue=dialogue_obj)
        else:
            emotion_object = emotion_objects[0]
            emotion_object.count = emotion_object.count + 1
            emotion_object.save()

        return JsonResponse({"message": "Mood Added"}, status=status.HTTP_200_OK)

    def remove_emoji(self, request, *args, **kwargs):

        # Get All Parameters
        try:
            dialogue = request.data["dialogue"]
            mood = request.data["mood"]
        except:
            return JsonResponse({"error": "Bad Parameters"}, status=status.HTTP_400_BAD_REQUEST)

        # Check If Emotion is present
        dialogue_obj = app_models.Dialogues.objects.get(id=dialogue)
        emotion_objects = app_models.Emotion.objects.filter(mood=mood, dialogue=dialogue_obj)
        if len(emotion_objects) == 0:
            return JsonResponse({"error": "Mood or Dialogue not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            emotion_object = emotion_objects[0]

            # Check emotion count
            count = emotion_object.count
            if count == 1:
                emotion_object.delete()
            else:
                emotion_object.count = emotion_object.count - 1
                emotion_object.save()

        return JsonResponse({"message": "Mood Removed"}, status=status.HTTP_200_OK)

    def add_dialogue(self, request, *args, **kwargs):

        # Get All Parameters
        try:
            movie = request.GET["movie"]
            year = request.GET["year"]
            dialogue = request.GET["dialogue"]
            star = request.GET["star"]
            tags = request.GET["tags"].split(',')
        except:
            return JsonResponse({"error": "Bad Parameters"}, status=status.HTTP_400_BAD_REQUEST)

        # Add Tag
        saved_tags = []
        for each_tag in tags:
            tag_ser = app_serializers.TagSerializer(data={
                'name': each_tag
            })
            if not tag_ser.is_valid():
                JsonResponse({"error": "Tag Invalid"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                tag_obj = tag_ser.save()
                saved_tags.append(tag_obj)

        # Add Dialog
        data = {
            'dialogue': dialogue,
            'movie_name': movie,
            'star': star,
            'movie_year': year
        }
        dialogue_ser = app_serializers.DialogueSerializer(data=data)

        if not dialogue_ser.is_valid():
            JsonResponse({"error": "Dialogue Invalid"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            dialogue_obj = dialogue_ser.save()

        # Tag Mapping
        for each_tag in saved_tags:
            (tag_mapping_obj, created) = app_models.TagMapping.objects.get_or_create(dialogue=dialogue_obj, tag=each_tag)

        return JsonResponse({"message": "Dialogue Added"}, status=status.HTTP_200_OK)
