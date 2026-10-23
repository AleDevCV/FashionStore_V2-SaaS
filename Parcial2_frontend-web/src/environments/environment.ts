/**
 * Configuración de entorno para compilaciones de PRODUCCIÓN.
 *
 * Al desplegar en la nube (requisito del examen: no usar localhost en la
 * defensa) hay que reemplazar `apiUrl` por el dominio público del backend.
 */
export const environment = {
  produccion: true,

  /** URL base de la API REST de FastAPI (relativa para Nginx reverse proxy). */
  apiUrl: '',

  /** Clave con la que se guarda el token JWT en el localStorage del navegador. */
  claveTokenJwt: 'fashionstore_p2_token',

  snapCameraKit: {
    appId: 'fe230af1-b5cd-48b6-83b0-8c3f664b71b4',
    apiToken: '',
    lensGroupId: '3936c886-4aa9-402e-9cf1-a6d72e708259', 
    testLensId: '05287a80-d455-4317-807b-314a336d7a59' 
  }
};
