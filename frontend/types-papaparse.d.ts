declare module 'papaparse' {
  const Papa: {
    unparse(data: unknown[] | Record<string, unknown>[]): string;
  };

  export default Papa;
}