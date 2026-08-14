package com.knowledgehub.api;

import com.amazonaws.serverless.exceptions.ContainerInitializationException;
import com.amazonaws.serverless.proxy.model.AwsProxyResponse;
import com.amazonaws.serverless.proxy.model.HttpApiV2ProxyRequest;
import com.amazonaws.serverless.proxy.spring.SpringBootLambdaContainerHandler;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestStreamHandler;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * API Gateway (HTTP API・ペイロード v2.0) からのリクエストを Spring Boot に橋渡しする
 * Lambda ハンドラ。REST API (v1.0) を使う場合は getAwsProxyHandler に変更すること。
 * ローカル実行 (mvn spring-boot:run) では使われず、Lambda デプロイ時のみ入口になる。
 */
public class StreamLambdaHandler implements RequestStreamHandler {

    private static final SpringBootLambdaContainerHandler<HttpApiV2ProxyRequest, AwsProxyResponse> handler;

    static {
        try {
            handler = SpringBootLambdaContainerHandler.getHttpApiV2ProxyHandler(KnowledgeHubApplication.class);
        } catch (ContainerInitializationException e) {
            throw new IllegalStateException("Spring Boot コンテナの初期化に失敗", e);
        }
    }

    @Override
    public void handleRequest(InputStream input, OutputStream output, Context context) throws IOException {
        handler.proxyStream(input, output, context);
    }
}
