self.__BUILD_MANIFEST = {
  "polyfillFiles": [
    "static/chunks/polyfills.js"
  ],
  "devFiles": [
    "static/chunks/react-refresh.js"
  ],
  "ampDevFiles": [],
  "lowPriorityFiles": [],
  "rootMainFiles": [],
  "rootMainFilesTree": {},
  "pages": {
    "/_app": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/_app.js"
    ],
    "/_error": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/_error.js"
    ],
    "/auth/login": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/auth/login.js"
    ],
    "/auth/signup": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/auth/signup.js"
    ],
    "/dashboard": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/dashboard.js"
    ],
    "/document/create": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/document/create.js"
    ],
    "/document/update": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/document/update.js"
    ],
    "/sickleave/create": [
      "static/chunks/webpack.js",
      "static/chunks/main.js",
      "static/chunks/pages/sickleave/create.js"
    ]
  },
  "ampFirstPages": []
};
self.__BUILD_MANIFEST.lowPriorityFiles = [
"/static/" + process.env.__NEXT_BUILD_ID + "/_buildManifest.js",
,"/static/" + process.env.__NEXT_BUILD_ID + "/_ssgManifest.js",

];