import SwiftUI

/// Third-party verifier screen allowing employers and institutions to verify credentials.
public struct VerifierView: View {
    @ObservedObject var viewModel: VerifierViewModel

    public init(viewModel: VerifierViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    StatusBanner()

                    // Instruction Header
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Third-Party Credential Verification")
                            .font(.headline)
                        Text("Enter the verification token or scan an applicant's QR badge. The system verifies authenticity without exposing sensitive personal identifiers.")
                            .font(.caption)
                            .foregroundColor(.inkMuted)
                    }
                    .padding(.horizontal, 16)
                    .frame(maxWidth: .infinity, alignment: .leading)

                    // Input Form
                    VStack(spacing: 12) {
                        TextField("Enter verification token (e.g. tok_s3_8f9a2b1c4e)", text: $viewModel.tokenInput)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled(true)
                            .padding(12)
                            .background(Color.surfaceBackground)
                            .cornerRadius(8)
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.borderLine, lineWidth: 1))

                        PrimaryButton(
                            title: "Verify Credential",
                            iconName: "checkmark.shield",
                            isLoading: viewModel.isVerifying
                        ) {
                            Task {
                                await viewModel.verify()
                            }
                        }
                    }
                    .padding(.horizontal, 16)

                    if let err = viewModel.errorMessage {
                        Text(err)
                            .font(.caption)
                            .foregroundColor(.errorCrimson)
                            .padding(.horizontal, 16)
                    }

                    // Verdict Result
                    if let verdict = viewModel.verdict {
                        VStack(spacing: 14) {
                            HStack {
                                Image(systemName: verdict.isValid ? "checkmark.seal.fill" : "xmark.seal.fill")
                                    .font(.title)
                                    .foregroundColor(verdict.isValid ? .successGreen : .errorCrimson)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(verdict.isValid ? "VERIFIED CREDENTIAL" : "VERIFICATION FAILED")
                                        .font(.headline)
                                        .foregroundColor(verdict.isValid ? .successGreen : .errorCrimson)
                                    Text(verdict.message)
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                }
                                Spacer()
                            }

                            Divider()

                            VStack(spacing: 8) {
                                HStack {
                                    Text("Issuing Institution:")
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                    Spacer()
                                    Text(verdict.institutionName)
                                        .font(.caption.bold())
                                }
                                HStack {
                                    Text("Program:")
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                    Spacer()
                                    Text(verdict.program)
                                        .font(.caption.bold())
                                }
                                HStack {
                                    Text("Session:")
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                    Spacer()
                                    Text(verdict.session)
                                        .font(.caption.bold())
                                }
                                HStack {
                                    Text("Issue Date:")
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                    Spacer()
                                    Text(verdict.issueDate)
                                        .font(.caption.bold())
                                }
                                HStack {
                                    Text("Digital Seal:")
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                    Spacer()
                                    Text(verdict.sealType)
                                        .font(.caption2.monospaced())
                                        .foregroundColor(.brandPrimary)
                                }
                            }
                        }
                        .padding(18)
                        .background(Color.cardBackground)
                        .cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.borderLine, lineWidth: 1))
                        .padding(.horizontal, 16)
                    }
                }
                .padding(.vertical, 12)
            }
            .navigationTitle("Credential Verifier")
        }
    }
}

