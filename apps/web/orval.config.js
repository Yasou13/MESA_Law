module.exports = {
  mesaApi: {
    input: '../api/openapi.json',
    output: {
      mode: 'tags-split',
      target: 'src/api/endpoints',
      schemas: 'src/api/models',
      client: 'react-query',
      override: {
        mutator: {
          path: './src/lib/api/client.ts',
          name: 'customInstance',
        }
      }
    }
  }
};
