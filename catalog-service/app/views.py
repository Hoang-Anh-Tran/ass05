from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Voucher
from .serializers import VoucherSerializer


class VoucherListCreate(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        if code:
            try:
                voucher = Voucher.objects.get(code=code, active=True)
                return Response(VoucherSerializer(voucher).data)
            except Voucher.DoesNotExist:
                return Response({"error": "Voucher not found or inactive"}, status=404)
        vouchers = Voucher.objects.all().order_by('-created_at')
        return Response(VoucherSerializer(vouchers, many=True).data)

    def post(self, request):
        serializer = VoucherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class VoucherDetail(APIView):
    def get_object(self, pk):
        try:
            return Voucher.objects.get(pk=pk)
        except Voucher.DoesNotExist:
            return None

    def get(self, request, pk):
        voucher = self.get_object(pk)
        if not voucher:
            return Response({"error": "Voucher not found"}, status=404)
        return Response(VoucherSerializer(voucher).data)

    def put(self, request, pk):
        voucher = self.get_object(pk)
        if not voucher:
            return Response({"error": "Voucher not found"}, status=404)
        serializer = VoucherSerializer(voucher, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        voucher = self.get_object(pk)
        if not voucher:
            return Response({"error": "Voucher not found"}, status=404)
        voucher.delete()
        return Response({"message": "Deleted"}, status=204)
