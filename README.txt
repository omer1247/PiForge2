PIFORGE - BASLANGIC
===================

YERELDE CALISTIRMA
1) PiForge klasorunu bilgisayarinda bir yere cikart.
2) BASLA.bat dosyasina cift tikla.
3) Ilk calistirmada mpmath kutuphanesi kurulur.
4) Tarayicida http://127.0.0.1:8000 adresini ac.
5) Hesaplama motorundan birini sec:
   - Tarayici: Hesaplama ziyaretcinin kendi bilgisayarinda yapilir. Bu modda limit 100.000 basamak.
   - Sunucu: Hesaplama PiForge'u calistiran sunucuda yapilir. Yerelde limit varsayilan olarak 2.000.000 basamak.
6) Tam sonuc yerel sunucu modunda PiForge/results klasorune TXT olarak kaydedilir. Tarayici modunda TXT indir dugmesini kullan.
7) Programi durdurmak icin terminal penceresinde Ctrl+C yap.

INTERNETTE YAYINLAMA (GITHUB + RENDER)
1) GitHub'da yeni bir repository olustur. Ornegin: PiForge
2) Bu klasordeki dosyalari repository'ye yukle. __pycache__ veya .pyc dosyalarini yukleme.
3) Render hesabina gir ve New + > Blueprint secenegini ac.
4) GitHub repository'ni bagla. Render, render.yaml dosyasini okuyup web servisini kurar.
5) Deploy tamamlandiginda Render'in verdigi https://...onrender.com adresini ziyaret et.
6) Render'in ucretsiz servisi bos kaldiginda uykuya girebilir; ilk acilis biraz zaman alabilir.

INTERNETTEKI SINIRLAR
- render.yaml sunucu hesaplamasini 100.000 basamakla sinirlar; bu, herkese acik servisin kaynaklarini korumak icindir.
- Tarayici modu 100.000 basamakla sinirlidir ve ziyaretcinin bilgisayarini kullanir.
- Yerelde calistirirken sunucu limiti varsayilan olarak 2.000.000 basamaktir.
- Tarayici modundaki hesaplama sunucuya kaydedilmez. Kullanici sonucu TXT olarak indirebilir.
- Herkese acik bir siteyi yayina almadan once test et. Buyuk hesaplamalar kaynak tuketebilir.
