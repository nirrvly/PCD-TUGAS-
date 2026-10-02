# Tugas 6 --- Analisis Thresholding untuk Deteksi Tanda Tangan

## Analisis Thresholding

### 1. Mengapa Thresholding Diperlukan Sebelum Melakukan Analisis Keberadaan Tanda Tangan?

Thresholding diperlukan untuk memisahkan objek atau **foreground** dari
**background** pada citra sehingga keberadaan tanda tangan dapat
dianalisis secara lebih terukur. Citra awal masih memiliki berbagai
tingkat intensitas dan terdiri dari objek yang berbeda, seperti tanda
tangan, tulisan, garis, maupun tekstur background. Oleh karena itu,
tanda tangan tidak dapat langsung dianalisis hanya berdasarkan citra
aslinya.

Melalui proses thresholding, citra grayscale diubah menjadi citra biner
sehingga piksel tertentu dikategorikan sebagai foreground dan piksel
lainnya sebagai background. Hasil segmentasi tersebut kemudian dapat
digunakan untuk menghitung karakteristik area, salah satunya adalah
jumlah dan persentase foreground pixel.

Berdasarkan hasil pengujian yang dilakukan, terdapat perbedaan jumlah
foreground pada beberapa kondisi citra.

#### Hasil pada crop awal

  Metode       Foreground Pixel   Total Pixel   Foreground (%)
  ---------- ------------------ ------------- ----------------
  Global                 31.893       650.056            4,91%
  Otsu                   38.520       650.056            5,93%
  Adaptive               40.373       650.056            6,21%

Setelah area dipersempit sehingga lebih fokus pada tanda tangan,
hasilnya berubah menjadi:

#### Hasil pada crop yang lebih fokus pada tanda tangan

  Metode       Foreground Pixel   Total Pixel   Foreground (%)
  ---------- ------------------ ------------- ----------------
  Global                 20.782       302.994            6,86%
  Otsu                   24.796       302.994            8,18%
  Adaptive               25.887       302.994            8,54%

Perubahan tersebut menunjukkan bahwa hasil thresholding dipengaruhi oleh
area yang dianalisis. Pada crop yang lebih fokus pada tanda tangan,
persentase foreground meningkat karena area yang dianalisis lebih banyak
berisi objek berupa goresan tanda tangan.

Namun, hasil pengujian pada citra **tanpa tanda tangan** menunjukkan
bahwa thresholding saja belum cukup untuk menentukan keberadaan tanda
tangan. Pada citra tanpa tanda tangan diperoleh:

#### Hasil pada citra tanpa tanda tangan

  Metode       Foreground Pixel   Total Pixel   Foreground (%)
  ---------- ------------------ ------------- ----------------
  Global                207.765     5.248.482            3,96%
  Otsu                  227.681     5.248.482            4,34%
  Adaptive              224.825     5.248.482            4,28%

Walaupun citra tersebut tidak memiliki tanda tangan, proses Otsu tetap
menghasilkan **4,34% foreground**. Hal ini terjadi karena foreground
yang terdeteksi tidak selalu merupakan tanda tangan. Tulisan, logo,
garis, dan elemen lain pada dokumen juga dapat dianggap sebagai
foreground oleh proses thresholding.

Dengan demikian, thresholding diperlukan sebagai **tahap segmentasi
awal**, tetapi jumlah foreground pixel saja belum cukup untuk memastikan
bahwa foreground tersebut merupakan tanda tangan. Diperlukan pemilihan
ROI yang tepat dan aturan klasifikasi yang sesuai agar sistem dapat
membedakan tanda tangan dari elemen lain pada dokumen.

------------------------------------------------------------------------

### 2. Apa Masalah yang Terjadi Jika Threshold Terlalu Tinggi atau Terlalu Rendah?

Nilai threshold sangat memengaruhi proses pemisahan foreground dan
background. Berdasarkan hasil pengujian, perubahan metode thresholding
menghasilkan perbedaan jumlah foreground pixel pada setiap citra.

#### Threshold terlalu tinggi

Threshold yang terlalu tinggi dapat menyebabkan lebih banyak piksel
dengan intensitas tertentu dikategorikan sebagai foreground. Akibatnya,
elemen yang sebenarnya bukan tanda tangan, seperti tulisan, tekstur,
noise, atau bagian background, dapat ikut masuk ke dalam hasil
segmentasi.

Hal tersebut dapat menyebabkan jumlah foreground pixel menjadi terlalu
besar. Kondisi ini terlihat pada hasil pengujian citra tanpa tanda
tangan. Meskipun tidak terdapat tanda tangan, metode Otsu tetap
menghasilkan **227.681 foreground pixel atau 4,34%**.

Karena batas keputusan yang digunakan adalah **2,00%**, nilai 4,34%
tersebut menyebabkan sistem memberikan hasil:

`SIGNATURE PRESENT`

Padahal kondisi sebenarnya adalah tidak terdapat tanda tangan. Hal ini
merupakan contoh **false positive**, yaitu sistem mendeteksi tanda
tangan ketika sebenarnya tanda tangan tidak ada.

Dengan demikian, foreground yang tinggi tidak selalu menunjukkan adanya
tanda tangan karena foreground juga dapat berasal dari teks, logo, atau
elemen lain pada dokumen.

#### Threshold terlalu rendah

Sebaliknya, threshold yang terlalu rendah dapat menyebabkan bagian tanda
tangan yang memiliki intensitas lebih terang atau goresan yang tipis
tidak terdeteksi sebagai foreground. Akibatnya, sebagian bentuk tanda
tangan dapat hilang atau menjadi terputus.

Jika jumlah foreground menjadi terlalu kecil, persentasenya dapat berada
di bawah batas keputusan sistem. Kondisi tersebut dapat menyebabkan
citra yang sebenarnya memiliki tanda tangan diklasifikasikan sebagai:

`SIGNATURE ABSENT`

Hal ini merupakan **false negative**, yaitu sistem tidak mendeteksi
tanda tangan meskipun tanda tangan sebenarnya ada.

Oleh karena itu, threshold yang digunakan harus mampu mempertahankan
bagian penting dari tanda tangan sekaligus mengurangi background, noise,
dan tulisan lain yang bukan merupakan tanda tangan.

------------------------------------------------------------------------

## Analisis Berdasarkan Ketiga Kondisi Pengujian

Hasil eksperimen menunjukkan adanya perbedaan karakteristik foreground
antara crop yang berbeda. Pada crop yang lebih fokus pada tanda tangan,
metode Otsu menghasilkan **8,18% foreground**, sedangkan pada citra
tanpa tanda tangan menghasilkan **4,34% foreground**.

Perbedaan tersebut menunjukkan bahwa persentase foreground pada area
tanda tangan memang lebih tinggi pada pengujian ini. Namun, terdapat
**tumpang tindih nilai foreground** antara citra yang memiliki tanda
tangan dan citra yang tidak memiliki tanda tangan. Citra tanpa tanda
tangan masih menghasilkan 4,34% foreground.

Hal ini menunjukkan bahwa aturan sederhana:

> Jika foreground \>= 2%, maka `SIGNATURE PRESENT`

belum mampu membedakan kedua kondisi dengan baik. Berdasarkan data yang
diperoleh, aturan tersebut menghasilkan `SIGNATURE PRESENT` baik pada
citra yang memiliki tanda tangan maupun pada citra yang sebenarnya tidak
memiliki tanda tangan.

Oleh karena itu, hasil eksperimen menunjukkan bahwa **thresholding
diperlukan untuk melakukan segmentasi, tetapi persentase foreground saja
belum cukup sebagai satu-satunya fitur untuk menentukan keberadaan tanda
tangan**. Sistem dapat dikembangkan dengan menggunakan ROI yang lebih
spesifik pada lokasi tanda tangan atau menambahkan karakteristik lain,
seperti luas objek terbesar, jumlah connected components, posisi objek,
atau bentuk area hasil segmentasi.

------------------------------------------------------------------------

## Ringkasan Hasil Pengujian

  Kondisi            Otsu Foreground Hasil Sistem        Kondisi Sebenarnya
  ---------------- ----------------- ------------------- --------------------
  Crop awal                    5,93% SIGNATURE PRESENT   Ada TTD
  Crop fokus TTD               8,18% SIGNATURE PRESENT   Ada TTD
  Tidak ada TTD                4,34% SIGNATURE PRESENT   Tidak ada TTD

Hasil tersebut menunjukkan bahwa sistem saat ini mengalami **false
positive pada citra tanpa tanda tangan**.

Decision threshold sebesar **2,00%** belum mampu membedakan citra yang
memiliki tanda tangan dan citra yang tidak memiliki tanda tangan karena
foreground pada citra tanpa tanda tangan masih mencapai **4,34%**.

## Kesimpulan

Thresholding merupakan tahap penting dalam proses deteksi tanda tangan
karena memungkinkan citra grayscale disegmentasi menjadi foreground dan
background. Hasil segmentasi kemudian dapat digunakan untuk menghitung
jumlah dan persentase foreground sebagai salah satu karakteristik citra.

Dari hasil pengujian, metode Otsu menghasilkan foreground sebesar
**5,93%** pada crop awal dan meningkat menjadi **8,18%** pada crop yang
lebih fokus pada tanda tangan. Sementara itu, citra tanpa tanda tangan
masih menghasilkan foreground sebesar **4,34%**.

Hasil tersebut menunjukkan bahwa foreground tidak selalu berasal dari
tanda tangan. Teks, logo, garis, noise, dan elemen lain pada dokumen
juga dapat terdeteksi sebagai foreground. Oleh karena itu, thresholding
dan persentase foreground saja belum cukup untuk membangun sistem
deteksi tanda tangan yang akurat.

Selain itu, threshold yang terlalu tinggi dapat memasukkan lebih banyak
background atau noise sebagai foreground, sedangkan threshold yang
terlalu rendah dapat menghilangkan sebagian goresan tanda tangan.
Pemilihan threshold dan ROI yang tepat sangat penting untuk memperoleh
segmentasi yang sesuai.

Pada pengujian ini, aturan `foreground >= 2%` menghasilkan **SIGNATURE
PRESENT** pada semua kondisi yang diuji, termasuk citra tanpa tanda
tangan. Dengan demikian, aturan tersebut masih perlu diperbaiki dan
sistem dapat dikembangkan dengan menggunakan ROI yang lebih spesifik
serta fitur tambahan seperti connected components, luas objek terbesar,
posisi objek, atau karakteristik bentuk tanda tangan.
