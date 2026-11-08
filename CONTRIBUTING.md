# Panduan Kontribusi (Contributing Guidelines)

Terima kasih atas minat Anda untuk berkontribusi pada pengembangan Anoterra IDE. Kami sangat mengapresiasi setiap masukan, perbaikan bug, maupun penambahan fitur baru yang dibawa oleh komunitas.

Agar proses kolaborasi berjalan tertib, profesional, dan menjaga kualitas kode, mohon perhatikan dan ikuti ketentuan di bawah ini sebelum mengirimkan kontribusi Anda.

## Aturan dan Ketentuan Kontribusi (Contribution Rules)

1. **Etika dan Profesionalisme**: Seluruh diskusi, laporan isu (*issue*), dan ulasan kode (*pull request*) wajib dilakukan menggunakan bahasa yang sopan, formal, objektif, dan profesional.
2. **Kualitas dan Kebersihan Kode**:
   - Kode sumber harus ditulis dengan rapi.
   - Pastikan kode Anda konsisten dengan struktur modular proyek
3. **Pengujian Fungsionalitas**: Sebelum membuat *Pull Request*, pastikan bahwa seluruh perubahan yang Anda buat telah diuji secara lokal baik di lingkungan sistem operasi Windows maupun Linux guna mencegah *regression error*.
4. **Fokus Perubahan**: Satu *Pull Request* sebaiknya hanya menangani satu perbaikan atau satu fitur spesifik. Jangan menggabungkan berbagai perbaikan yang tidak berkaitan dalam satu pengajuan.

## Alur Kerja Kontribusi (Workflow)

1. **Fork Repositori**: Buat salinan (*fork*) dari repositori utama Anoterra ke akun GitHub Anda.
2. **Buat Cabang (Branch)**: Buat *branch* baru dengan nama yang deskriptif berdasarkan topik kontribusi Anda.
   ```bash
   git checkout -b fitur/nama-fitur-anda
   ```
   atau untuk perbaikan bug:
   ```bash
   git checkout -b perbaikan/nama-bug-anda
   ```
3. **Lakukan Perubahan**: Lakukan *commit* pada perubahan Anda dengan pesan *commit* yang jelas, deskriptif, dan menggunakan format imperatif (contoh: `Menambahkan fitur lanjutan pada panel editor`).
4. **Kirim Perubahan (Push)**: Unggah *branch* Anda ke repositori *fork* Anda:
   ```bash
   git origin push fitur/nama-fitur-anda
   ```
5. **Buat Pull Request (PR)**: Buka halaman repositori utama dan ajukan *Pull Request* ke *branch* utama. Berikan penjelasan yang mendetail mengenai latar belakang perubahan dan cara menguji fitur atau perbaikan tersebut.

Setiap kontribusi akan ditinjau secara berkala oleh pengelola utama. Terima kasih telah membantu menjadikan Anoterra sebagai IDE lintas platform yang handal.

~ Array