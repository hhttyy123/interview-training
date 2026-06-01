class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.chunks = [];
    this.sampleCount = 0;
  }

  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel) {
      this.chunks.push(new Float32Array(channel));
      this.sampleCount += channel.length;
      if (this.sampleCount >= 2048) {
        const combined = new Float32Array(this.sampleCount);
        let offset = 0;
        for (const chunk of this.chunks) {
          combined.set(chunk, offset);
          offset += chunk.length;
        }
        this.port.postMessage(combined);
        this.chunks = [];
        this.sampleCount = 0;
      }
    }
    return true;
  }
}

registerProcessor("pcm-capture-processor", PcmCaptureProcessor);
