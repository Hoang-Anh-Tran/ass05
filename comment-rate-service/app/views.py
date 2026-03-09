from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CommentRate
from .serializers import CommentRateSerializer

class CommentListCreate(APIView):
    def get(self, request):
        book_id = request.query_params.get("book_id")
        if book_id:
            comments = CommentRate.objects.filter(book_id=book_id)
        else:
            comments = CommentRate.objects.all()
        return Response(CommentRateSerializer(comments, many=True).data)

    def post(self, request):
        serializer = CommentRateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
