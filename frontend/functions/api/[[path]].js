export async function onRequest(context) {
  const { request, env } = context;

  if (env.API) {
    return env.API.fetch(request);
  }

  const url = new URL(request.url);
  const target = `https://boke-n-backend.liumeng191549149.workers.dev${url.pathname}${url.search}`;
  return fetch(target, request);
}
