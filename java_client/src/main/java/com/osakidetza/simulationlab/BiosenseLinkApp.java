package com.osakidetza.simulationlab;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.data.time.Millisecond;
import org.jfree.data.time.TimeSeries;
import org.jfree.data.time.TimeSeriesCollection;

import javax.swing.*;
import java.awt.*;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class BiosenseLinkApp extends JFrame {

    private CardLayout cardLayout;
    private JPanel mainPanel;
    private JPanel loginPanel;
    private JPanel dashboardPanel;

    private TimeSeries ecgSeries;
    private WebSocketClient webSocketClient;
    
    private JLabel lblUser;
    private JLabel lblRole;

    public BiosenseLinkApp() {
        setTitle("BiosenseLink - Consola Clínica (Java Swing)");
        setSize(1000, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        cardLayout = new CardLayout();
        mainPanel = new JPanel(cardLayout);

        buildLoginPanel();
        buildDashboardPanel();

        mainPanel.add(loginPanel, "LOGIN");
        mainPanel.add(dashboardPanel, "DASHBOARD");

        add(mainPanel);
        cardLayout.show(mainPanel, "LOGIN");
    }

    private void buildLoginPanel() {
        loginPanel = new JPanel(new GridBagLayout());
        loginPanel.setBackground(new Color(15, 23, 42)); // Tailwind slate-900

        JPanel formPanel = new JPanel(new GridLayout(4, 1, 10, 10));
        formPanel.setBackground(new Color(30, 41, 59)); // Tailwind slate-800
        formPanel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));

        JLabel title = new JLabel("BiosenseLink Login", SwingConstants.CENTER);
        title.setForeground(Color.WHITE);
        title.setFont(new Font("Arial", Font.BOLD, 24));

        JTextField pinField = new JPasswordField();
        pinField.setHorizontalAlignment(JTextField.CENTER);
        pinField.setFont(new Font("Arial", Font.PLAIN, 18));
        
        JButton loginButton = new JButton("Ingresar");
        loginButton.setBackground(new Color(59, 130, 246)); // Tailwind blue-500
        loginButton.setForeground(Color.WHITE);
        loginButton.setFont(new Font("Arial", Font.BOLD, 16));

        JLabel errorLabel = new JLabel(" ", SwingConstants.CENTER);
        errorLabel.setForeground(Color.RED);

        loginButton.addActionListener(e -> {
            String pin = pinField.getText();
            authenticate(pin, errorLabel);
        });

        formPanel.add(title);
        formPanel.add(pinField);
        formPanel.add(loginButton);
        formPanel.add(errorLabel);

        loginPanel.add(formPanel);
    }

    private void authenticate(String pin, JLabel errorLabel) {
        new Thread(() -> {
            try {
                URL url = new URL("http://localhost:8000/api/auth");
                HttpURLConnection con = (HttpURLConnection) url.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setDoOutput(true);

                String jsonInputString = "{\"pin\": \"" + pin + "\"}";

                try (OutputStream os = con.getOutputStream()) {
                    byte[] input = jsonInputString.getBytes(StandardCharsets.UTF_8);
                    os.write(input, 0, input.length);
                }

                int code = con.getResponseCode();
                if (code == 200) {
                    try (InputStreamReader reader = new InputStreamReader(con.getInputStream(), StandardCharsets.UTF_8)) {
                        Gson gson = new Gson();
                        JsonObject response = gson.fromJson(reader, JsonObject.class);
                        if (response.get("status").getAsString().equals("ok")) {
                            String displayName = response.get("display_name").getAsString();
                            String role = response.get("title").getAsString();
                            
                            SwingUtilities.invokeLater(() -> {
                                lblUser.setText(displayName);
                                lblRole.setText(role);
                                cardLayout.show(mainPanel, "DASHBOARD");
                                connectWebSocket();
                            });
                        } else {
                            SwingUtilities.invokeLater(() -> errorLabel.setText(response.get("message").getAsString()));
                        }
                    }
                } else {
                    SwingUtilities.invokeLater(() -> errorLabel.setText("Error HTTP: " + code));
                }
            } catch (Exception ex) {
                ex.printStackTrace();
                SwingUtilities.invokeLater(() -> errorLabel.setText("Error de red conectando al backend"));
            }
        }).start();
    }

    private void buildDashboardPanel() {
        dashboardPanel = new JPanel(new BorderLayout());
        dashboardPanel.setBackground(Color.DARK_GRAY);

        // Header
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(new Color(15, 23, 42));
        header.setBorder(BorderFactory.createEmptyBorder(10, 20, 10, 20));

        JLabel title = new JLabel("Monitorización ECG - Tiempo Real");
        title.setForeground(Color.WHITE);
        title.setFont(new Font("Arial", Font.BOLD, 20));

        JPanel userInfo = new JPanel(new GridLayout(2, 1));
        userInfo.setBackground(new Color(15, 23, 42));
        lblUser = new JLabel("Usuario");
        lblUser.setForeground(Color.GREEN);
        lblRole = new JLabel("Rol");
        lblRole.setForeground(Color.LIGHT_GRAY);
        userInfo.add(lblUser);
        userInfo.add(lblRole);

        header.add(title, BorderLayout.WEST);
        header.add(userInfo, BorderLayout.EAST);

        // Chart
        ecgSeries = new TimeSeries("ECG Signal");
        TimeSeriesCollection dataset = new TimeSeriesCollection(ecgSeries);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                "", "", "Amplitud (mV)", dataset, false, false, false);

        chart.setBackgroundPaint(Color.BLACK);
        chart.getPlot().setBackgroundPaint(Color.BLACK);
        chart.getXYPlot().getDomainAxis().setTickLabelsVisible(false);
        chart.getXYPlot().getRangeAxis().setRange(-1.5, 1.5);
        chart.getXYPlot().getRenderer().setSeriesPaint(0, Color.GREEN);

        ChartPanel chartPanel = new ChartPanel(chart);
        
        dashboardPanel.add(header, BorderLayout.NORTH);
        dashboardPanel.add(chartPanel, BorderLayout.CENTER);
    }

    private void connectWebSocket() {
        try {
            webSocketClient = new WebSocketClient(new URI("ws://localhost:8000/ws/ecg")) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    System.out.println("WebSocket Conectado");
                }

                @Override
                public void onMessage(String message) {
                    try {
                        Gson gson = new Gson();
                        JsonObject data = gson.fromJson(message, JsonObject.class);
                        if (data.has("type") && data.get("type").getAsString().equals("ecg_stream")) {
                            JsonObject leads = data.getAsJsonObject("leads");
                            if (leads != null && leads.has("I")) {
                                com.google.gson.JsonArray leadI = leads.getAsJsonArray("I");
                                
                                SwingUtilities.invokeLater(() -> {
                                    for (int i = 0; i < leadI.size(); i++) {
                                        double value = leadI.get(i).getAsDouble();
                                        ecgSeries.addOrUpdate(new Millisecond(), value);
                                    }
                                    
                                    // Mantener solo los últimos 500 puntos para simular el barrido del osciloscopio
                                    if (ecgSeries.getItemCount() > 500) {
                                        ecgSeries.delete(0, ecgSeries.getItemCount() - 501);
                                    }
                                });
                            }
                        }
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    System.out.println("WebSocket Desconectado");
                }

                @Override
                public void onError(Exception ex) {
                    ex.printStackTrace();
                }
            };
            webSocketClient.connect();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new BiosenseLinkApp().setVisible(true);
        });
    }
}
