import type { AppProps } from 'next/app';
import Head from 'next/head';

import '../index.css';

export default function RevenueMindApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>RevenueMind Pricing Copilot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Component {...pageProps} />
    </>
  );
}
