/**
 * Configuración de entorno para DESARROLLO local.
 *
 * Apunta al contenedor Docker del backend de FastAPI, publicado por
 * docker-compose en el puerto 8000 de la máquina anfitriona.
 *
 * Angular sustituye automáticamente environment.ts por este archivo cuando se
 * compila con la configuración `development` (ver fileReplacements en
 * angular.json).
 */
export const environment = {
  produccion: false,

  /** URL base de la API REST de FastAPI levantada con docker compose. */
  apiUrl: 'http://localhost:8000',

  /** Clave con la que se guarda el token JWT en el localStorage del navegador. */
  claveTokenJwt: 'fashionstore_p2_token',

  snapCameraKit: {
    appId: 'fe230af1-b5cd-48b6-83b0-8c3f664b71b4',
    apiToken: '',
    lensGroupId: '3936c886-4aa9-402e-9cf1-a6d72e708259',
    testLensId: '05287a80-d455-4317-807b-314a336d7a59'
  }
};
