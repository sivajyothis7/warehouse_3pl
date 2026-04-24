// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://warehouse-3pl-docs.vercel.app",
  integrations: [
    starlight({
      title: "Warehouse 3PL",
      description:
        "3PL Warehouse Management System — multi-client operations on ERPNext.",
      favicon: "/favicon.svg",
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/sivajyothis7/warehouse_3pl",
        },
      ],
      editLink: {
        baseUrl:
          "https://github.com/sivajyothis7/warehouse_3pl/edit/develop/docs-site/",
      },
      lastUpdated: true,
      customCss: ["./src/styles/custom.css"],
      sidebar: [
        {
          label: "Start Here",
          items: [
            { label: "Overview", link: "/" },
            { label: "Getting Started", link: "/getting-started/" },
            { label: "Installation", link: "/installation/" },
          ],
        },
        {
          label: "User Guide",
          items: [
            { label: "How it works", link: "/user/overview/" },
            { label: "Inbound — Receiving", link: "/user/inbound/" },
            { label: "Outbound — Fulfillment", link: "/user/outbound/" },
            { label: "Warehouse Job Record", link: "/user/warehouse-job/" },
            { label: "Billing & Rate Cards", link: "/user/billing/" },
          ],
        },
        {
          label: "Developer Guide",
          items: [
            { label: "Architecture", link: "/guide/architecture/" },
            { label: "Doctypes", link: "/guide/doctypes/" },
            { label: "End-to-End Flow", link: "/guide/end-to-end-flow/" },
            { label: "Utility Engines", link: "/guide/engines/" },
            { label: "Customisation", link: "/guide/customisation/" },
          ],
        },
        {
          label: "Reference",
          items: [
            { label: "Master Data", link: "/reference/master-data/" },
            { label: "Policy Engine", link: "/reference/policy-engine/" },
            { label: "Billing Reference", link: "/reference/billing/" },
            { label: "Custom Fields", link: "/reference/custom-fields/" },
          ],
        },
      ],
    }),
  ],
});
