# RunPod + ComfyUI + LTX-2.3

Bu klasör, RunPod GPU Pod üzerinde ComfyUI ve Lightricks LTX-2.3 kurulumu için hazırlanmıştır.

## Gereksinim

- RunPod hesabı ve aktif ödeme yöntemi gerekir.
- LTX-2.3 için tercihen **48 GB veya daha fazla VRAM** seçin; tam 22B model için resmî gereksinim 32 GB+ VRAM'dir.
- Model ağırlıkları için en az 100 GB kalıcı disk ayırın.
- RunPod'da ComfyUI veya PyTorch tabanlı bir template seçin.

## Pod içinde kurulum

```bash
git clone https://github.com/fahrimert99-cmd/ASMR.git /workspace/ASMR
cd /workspace/ASMR
chmod +x runpod/*.sh
COMFYUI_ROOT=/workspace/ComfyUI DOWNLOAD_MODELS=0 ./runpod/install_comfyui_ltx23.sh
./runpod/start_comfyui.sh
```

Modelleri de indirmek için:

```bash
cd /workspace/ASMR
COMFYUI_ROOT=/workspace/ComfyUI DOWNLOAD_MODELS=1 ./runpod/install_comfyui_ltx23.sh
```

Hugging Face erişim anahtarı gerekiyorsa anahtarı terminal geçmişine yazmadan önce RunPod Secret olarak `HF_TOKEN` adıyla tanımlayın.

ComfyUI, Pod'un **8188** portundan çalışır. RunPod arayüzünde HTTP Service / Connect bağlantısını açın.

## LTX-2.3 workflow

Kurulumdan sonra ComfyUI içindeki Template Library'den:

- `Video > LTX-2.3 > Image to Video`
- `Video > LTX-2.3 > Text to Video`

şablonlarından birini seçin. Gönderilen karakter görselini `input` klasörüne yükleyip Image to Video workflow'unda kullanabilirsiniz.

## Maliyet kontrolü

İşiniz bitince Pod'u **Stop** veya **Terminate** edin. GPU kiralaması açık kaldığı sürece ücret yazabilir. Kalıcı disk ücretleri Pod kapalıyken de devam edebilir; gerekli dosyaları indirdikten sonra depolamayı da kontrol edin.
