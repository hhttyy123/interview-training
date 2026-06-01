export function downsampleToPcm16(input: Float32Array, inputRate: number, outputRate = 16000): ArrayBuffer {
  if (inputRate < outputRate) {
    throw new Error("Input sample rate cannot be lower than output sample rate.");
  }

  const ratio = inputRate / outputRate;
  const outputLength = Math.floor(input.length / ratio);
  const output = new Int16Array(outputLength);
  for (let outputIndex = 0; outputIndex < outputLength; outputIndex += 1) {
    const start = Math.floor(outputIndex * ratio);
    const end = Math.min(Math.floor((outputIndex + 1) * ratio), input.length);
    let sum = 0;
    for (let inputIndex = start; inputIndex < end; inputIndex += 1) {
      sum += input[inputIndex];
    }
    const average = sum / Math.max(end - start, 1);
    const clamped = Math.max(-1, Math.min(1, average));
    output[outputIndex] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
  }
  return output.buffer;
}
