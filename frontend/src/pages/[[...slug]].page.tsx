import type { GetStaticPaths, GetStaticProps } from 'next';

import ClientApp from '../ClientApp';

const staticPaths = [
  [],
  ['login'],
  ['sales'],
  ['sales', 'quotes', 'new'],
  ['dashboard'],
  ['products'],
  ['pricing'],
  ['upload-center'],
  ['approvals'],
  ['analytics'],
  ['admin'],
  ['profile'],
];

export const getStaticPaths: GetStaticPaths = async () => ({
  paths: staticPaths.map((slug) => ({ params: { slug } })),
  fallback: false,
});

export const getStaticProps: GetStaticProps = async () => ({
  props: {},
});

export default function AppRoute() {
  return <ClientApp />;
}
