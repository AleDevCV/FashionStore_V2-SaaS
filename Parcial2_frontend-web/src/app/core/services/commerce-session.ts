export const commerceSessionKey = 'fashionstore_p2_active';

export function commerceSession(): string | null {
  return sessionStorage.getItem(commerceSessionKey) ?? localStorage.getItem(commerceSessionKey);
}
