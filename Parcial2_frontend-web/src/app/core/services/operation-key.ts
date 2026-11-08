/** Reutiliza la clave de una solicitud mientras su contenido no cambie. */
export class OperationKey {
  private previous?: { payload: string; key: string };

  matches(payload: object): boolean {
    return this.previous?.payload === JSON.stringify(payload);
  }

  get(payload: object): string {
    const serialized = JSON.stringify(payload);
    if (this.previous?.payload !== serialized) {
      this.previous = { payload: serialized, key: crypto.randomUUID() };
    }
    return this.previous.key;
  }

  clear(): void {
    this.previous = undefined;
  }
}
