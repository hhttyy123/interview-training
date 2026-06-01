import { downsampleToPcm16 } from "./pcm-encoder";

export class MicrophoneStream {
  private stream?: MediaStream;
  private context?: AudioContext;
  private source?: MediaStreamAudioSourceNode;
  private processor?: AudioWorkletNode;
  private sink?: GainNode;

  constructor(private readonly onChunk: (chunk: ArrayBuffer) => void) {}

  async start(): Promise<void> {
    if (this.stream) return;

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
    this.context = new AudioContext();
    await this.context.audioWorklet.addModule("/pcm-capture-processor.js");
    this.source = this.context.createMediaStreamSource(this.stream);
    this.processor = new AudioWorkletNode(this.context, "pcm-capture-processor");
    this.sink = this.context.createGain();
    this.sink.gain.value = 0;
    this.processor.port.onmessage = (event: MessageEvent<Float32Array>) => {
      if (this.context) {
        this.onChunk(downsampleToPcm16(event.data, this.context.sampleRate));
      }
    };
    this.source.connect(this.processor);
    this.processor.connect(this.sink);
    this.sink.connect(this.context.destination);
  }

  async stop(): Promise<void> {
    this.processor?.disconnect();
    this.source?.disconnect();
    this.sink?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    await this.context?.close();
    this.stream = undefined;
    this.context = undefined;
    this.source = undefined;
    this.processor = undefined;
    this.sink = undefined;
  }
}
